import math
import numpy as np


def norma(v):
    return float(np.linalg.norm(v))


def unitario(v):
    v = np.asarray(v, dtype=float)
    n = norma(v)
    if n == 0:
        return np.zeros_like(v)
    return v / n


def campo_viento(posicion, rapidez_viento, angulo_grados, componente_vertical, k_altura):
    posicion = np.asarray(posicion, dtype=float)
    z = float(posicion[2])

    theta = math.radians(angulo_grados)
    factor = 1.0 + (k_altura * z / 100.0)

    return factor * np.array(
        [
            rapidez_viento * math.cos(theta),
            rapidez_viento * math.sin(theta),
            componente_vertical,
        ],
        dtype=float,
    )


def paso_rk4(funcion, posicion, dt):
    k1 = funcion(posicion)
    k2 = funcion(posicion + 0.5 * dt * k1)
    k3 = funcion(posicion + 0.5 * dt * k2)
    k4 = funcion(posicion + dt * k3)

    return posicion + (dt / 6.0) * (
        k1 + 2.0*k2 + 2.0*k3 + k4
    )


def trayectoria_ideal(p0, p1, rapidez_dron, n=280):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)

    desplazamiento = p1 - p0
    distancia = norma(desplazamiento)

    if distancia == 0:
        raise ValueError("El punto inicial y el punto final deben ser diferentes.")
    if rapidez_dron <= 0:
        raise ValueError("La rapidez del dron debe ser mayor que cero.")

    direccion = unitario(desplazamiento)
    velocidad = rapidez_dron * direccion
    tiempo_total = distancia / rapidez_dron

    t = np.linspace(0.0, tiempo_total, n)
    r = p0[None, :] + t[:, None] * velocidad[None, :]
    v = np.tile(velocidad, (n, 1))
    a = np.zeros_like(v)

    return {
        "t": t,
        "r": r,
        "v": v,
        "a": a,
        "distancia": distancia,
        "tiempo": tiempo_total,
        "v_dron": v,
    }


def _metricas(t, r, v, a, v_dron, viento, destino):
    segmentos = np.diff(r, axis=0)
    distancia = float(np.sum(np.linalg.norm(segmentos, axis=1)))
    desviacion = norma(r[-1] - destino)
    rapidez_media = float(np.mean(np.linalg.norm(v, axis=1)))
    aceleracion_media = float(np.mean(np.linalg.norm(a, axis=1)))

    # Indicador matematico de esfuerzo: velocidad y aceleracion.
    lambda_aceleracion = 0.2
    esfuerzo_velocidad = np.sum(
        v_dron**2,
        axis=1,
    )
    esfuerzo_aceleracion = np.sum(
        a**2,
        axis=1,
    )
    integrando = (
        esfuerzo_velocidad
        + lambda_aceleracion * esfuerzo_aceleracion
    )
    costo = float(
        np.trapezoid(
            integrando,
            t,
        )
    )

    return {
        "t": t,
        "r": r,
        "v": v,
        "a": a,
        "v_dron": v_dron,
        "viento": viento,
        "distancia": distancia,
        "desviacion": desviacion,
        "rapidez_media": rapidez_media,
        "aceleracion_media": aceleracion_media,
        "costo": costo,
    }


def trayectoria_con_viento(
    p0, p1, rapidez_dron, rapidez_viento, angulo_viento,
    componente_vertical, k_altura, n=280
):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)

    ideal = trayectoria_ideal(p0, p1, rapidez_dron, n)
    t = ideal["t"]
    dt = t[1] - t[0]

    direccion = unitario(p1 - p0)
    v_dron_constante = rapidez_dron * direccion

    r = np.zeros((n, 3))
    v = np.zeros((n, 3))
    viento = np.zeros((n, 3))
    v_dron = np.zeros((n, 3))
    r[0] = p0

    def f(pos):
        w = campo_viento(
            pos, rapidez_viento, angulo_viento,
            componente_vertical, k_altura
        )
        return v_dron_constante + w

    for i in range(n - 1):
        r[i + 1] = paso_rk4(f, r[i], dt)

    for i in range(n):
        w = campo_viento(
            r[i], rapidez_viento, angulo_viento,
            componente_vertical, k_altura
        )
        viento[i] = w
        v_dron[i] = v_dron_constante
        v[i] = v_dron_constante + w

    a = np.gradient(v, t, axis=0)

    return _metricas(t, r, v, a, v_dron, viento, p1)


def trayectoria_compensada(
    p0, p1, rapidez_dron, rapidez_viento, angulo_viento,
    componente_vertical, k_altura, n=280
):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)

    if (
        abs(rapidez_viento) < 1e-12
        and abs(componente_vertical) < 1e-12
    ):
        ideal = trayectoria_ideal(p0, p1, rapidez_dron, n)
        viento = np.zeros_like(ideal["r"])
        return {
            "t": ideal["t"],
            "r": ideal["r"].copy(),
            "v": ideal["v"].copy(),
            "a": ideal["a"].copy(),
            "v_dron": ideal["v_dron"].copy(),
            "viento": viento,
            "distancia": ideal["distancia"],
            "desviacion": 0.0,
            "rapidez_media": rapidez_dron,
            "aceleracion_media": 0.0,
            "costo": float(rapidez_dron**2 * ideal["tiempo"]),
        }

    ideal = trayectoria_ideal(p0, p1, rapidez_dron, n)
    t = ideal["t"]
    dt = t[1] - t[0]

    r = np.zeros((n, 3))
    v = np.zeros((n, 3))
    viento = np.zeros((n, 3))
    v_dron = np.zeros((n, 3))
    r[0] = p0

    def control(pos):
        error = p1 - pos

        w = campo_viento(
            pos, rapidez_viento, angulo_viento,
            componente_vertical, k_altura
        )

        if norma(error) < 0.15:
            comando = -w
        else:
            direccion_destino = unitario(error)
            v_deseada = rapidez_dron * direccion_destino
            comando = v_deseada - w

        if norma(comando) > rapidez_dron:
            comando = rapidez_dron * unitario(comando)

        return comando

    def f(pos):
        w = campo_viento(
            pos, rapidez_viento, angulo_viento,
            componente_vertical, k_altura
        )
        return control(pos) + w

    for i in range(n - 1):
        r[i + 1] = paso_rk4(f, r[i], dt)

    for i in range(n):
        w = campo_viento(
            r[i], rapidez_viento, angulo_viento,
            componente_vertical, k_altura
        )
        comando = control(r[i])

        viento[i] = w
        v_dron[i] = comando
        v[i] = comando + w

    a = np.gradient(v, t, axis=0)

    return _metricas(t, r, v, a, v_dron, viento, p1)
