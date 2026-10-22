import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modelo import (
    trayectoria_ideal,
    trayectoria_con_viento,
    trayectoria_compensada,
    campo_viento,
    norma,
)

st.set_page_config(
    page_title="Simulador de Trayectoria de un Dron",
    page_icon="🛸",
    layout="wide",
)

AZUL = "#42B6FF"
ROJO = "#FF6B6B"
DORADO = "#F4C95D"
VERDE = "#61DDAA"
MORADO = "#B69CFF"

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1500px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .hero {
        border: 1px solid rgba(255,255,255,.08);
        background:
            radial-gradient(circle at 87% 16%, rgba(244,201,93,.10), transparent 28%),
            linear-gradient(135deg, rgba(255,255,255,.03), rgba(255,255,255,.012));
        border-radius: 22px;
        padding: 27px 30px 24px;
        margin-bottom: 18px;
    }

    .eyebrow {
        color: #F4C95D;
        font-size: .83rem;
        font-weight: 800;
        letter-spacing: .06em;
        margin-bottom: 8px;
    }

    .hero-title {
        font-size: 2.15rem;
        font-weight: 790;
        line-height: 1.12;
        margin-bottom: 10px;
    }

    .hero-text {
        color: rgba(255,255,255,.73);
        line-height: 1.58;
    }

    .flow-card {
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 16px;
        padding: 17px 18px;
        min-height: 138px;
        background: rgba(255,255,255,.018);
    }

    .flow-number {
        color: #F4C95D;
        font-size: .78rem;
        font-weight: 800;
        letter-spacing: .06em;
        margin-bottom: 6px;
    }

    .flow-title {
        font-size: 1rem;
        font-weight: 730;
        margin-bottom: 6px;
    }

    .flow-text {
        color: rgba(255,255,255,.68);
        line-height: 1.45;
        font-size: .92rem;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 15px;
        padding: 12px 14px;
        background: rgba(255,255,255,.018);
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(255,255,255,.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">CÁLCULO MULTIVARIADO · MODELO EN ℝ³</div>
        <div class="hero-title">Trayectoria de un dron bajo la influencia del viento</div>
        <div class="hero-text">
            El simulador compara una trayectoria ideal, una trayectoria perturbada
            por un campo vectorial de viento y una trayectoria corregida.
            Todas las métricas y gráficas se recalculan automáticamente cuando
            cambian las coordenadas o cualquier parámetro del modelo.
            <br><br>
            <b>Ingeniería de Sistemas · CUN</b> · Mosquera Sanchez Kevin Julian · Camila Guarin Laverde
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Parámetros del modelo")
    st.caption(
        "Cambie los valores y los resultados se actualizan automáticamente."
    )

    st.subheader("A · Punto inicial")
    x0 = st.number_input("x₀ (m)", value=0.0, step=5.0)
    y0 = st.number_input("y₀ (m)", value=0.0, step=5.0)
    z0 = st.number_input("z₀ (m)", value=10.0, step=2.0)

    st.subheader("B · Punto destino")
    x1 = st.number_input("x₁ (m)", value=120.0, step=5.0)
    y1 = st.number_input("y₁ (m)", value=80.0, step=5.0)
    z1 = st.number_input("z₁ (m)", value=40.0, step=2.0)

    st.divider()

    st.subheader("Dron")
    rapidez_dron = st.slider(
        "Rapidez máxima (m/s)",
        1.0, 30.0, 12.0, 0.5
    )

    st.subheader("Viento")
    rapidez_viento = st.slider(
        "Rapidez horizontal (m/s)",
        0.0, 15.0, 7.0, 0.5
    )
    angulo = st.slider(
        "Dirección horizontal (°)",
        0, 360, 25, 5
    )
    vertical = st.slider(
        "Componente vertical (m/s)",
        -5.0, 5.0, 0.5, 0.25
    )
    k_altura = st.slider(
        "Variación con altura k",
        -1.0, 1.0, 0.30, 0.05
    )

inicio = np.array([x0, y0, z0], dtype=float)
destino = np.array([x1, y1, z1], dtype=float)

errores = []

if norma(destino - inicio) < 1e-9:
    errores.append("El punto inicial y el punto final deben ser diferentes.")

if z0 < 0 or z1 < 0:
    errores.append("La altitud z no puede ser negativa en este modelo.")

if rapidez_dron <= 0:
    errores.append("La rapidez del dron debe ser mayor que cero.")

if errores:
    for e in errores:
        st.error(e)
    st.stop()

if rapidez_viento > rapidez_dron:
    st.warning(
        "El viento supera la rapidez máxima del dron; "
        "la compensación puede ser insuficiente."
    )

ideal = trayectoria_ideal(
    inicio, destino, rapidez_dron
)

real = trayectoria_con_viento(
    inicio, destino, rapidez_dron,
    rapidez_viento, angulo, vertical, k_altura
)

corregida = trayectoria_compensada(
    inicio, destino, rapidez_dron,
    rapidez_viento, angulo, vertical, k_altura
)

mejora = (
    100 * (1 - corregida["desviacion"] / real["desviacion"])
    if real["desviacion"] > 1e-12
    else 0.0
)

st.subheader("Idea del proyecto")

c1, c2, c3, c4 = st.columns(4)

for col, num, titulo, texto in [
    (
        c1, "01 · POSICIÓN", "Definimos A y B",
        "El movimiento se representa mediante coordenadas x, y, z."
    ),
    (
        c2, "02 · MOVIMIENTO", "Calculamos la ruta ideal",
        "El dron intenta viajar desde A hasta B con una velocidad vectorial."
    ),
    (
        c3, "03 · PERTURBACIÓN", "Agregamos el viento",
        "El viento modifica el movimiento mediante un campo vectorial."
    ),
    (
        c4, "04 · CORRECCIÓN", "Compensamos el rumbo",
        "Se ajusta el vector del dron para reducir la desviación."
    ),
]:
    with col:
        st.markdown(
            f"""
            <div class="flow-card">
                <div class="flow-number">{num}</div>
                <div class="flow-title">{titulo}</div>
                <div class="flow-text">{texto}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Distancia ideal A → B", f"{ideal['distancia']:.1f} m")
m2.metric("Desviación sin corrección", f"{real['desviacion']:.1f} m")
m3.metric("Desviación corregida", f"{corregida['desviacion']:.1f} m")
if real["desviacion"] < 1e-9:
    m4.metric("Reducción de desviación", "No aplica")
else:
    m4.metric("Reducción de desviación", f"{mejora:.1f} %")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Resumen",
        "Simulación 2D",
        "Simulación 3D",
        "Modelo matemático",
        "Resultados",
    ]
)

with tab1:
    izquierda, derecha = st.columns([1.15, 1])

    with izquierda:
        st.subheader("Pregunta de investigación")
        st.write(
            "¿Cómo se pueden utilizar los vectores y las herramientas del "
            "cálculo multivariado para representar, analizar y corregir la "
            "trayectoria de un dron en un espacio tridimensional considerando "
            "la dirección y velocidad del viento?"
        )

        st.subheader("Objetivo")
        st.write(
            "Comparar una trayectoria ideal, una trayectoria afectada por el "
            "viento y una trayectoria corregida mediante compensación vectorial."
        )

    with derecha:
        st.subheader("Escenario actual")
        st.write(
            f"**Inicio:** ({x0:.1f}, {y0:.1f}, {z0:.1f}) m  \n"
            f"**Destino:** ({x1:.1f}, {y1:.1f}, {z1:.1f}) m  \n"
            f"**Rapidez del dron:** {rapidez_dron:.1f} m/s  \n"
            f"**Viento horizontal:** {rapidez_viento:.1f} m/s  \n"
            f"**Dirección del viento:** {angulo}°"
        )

        if real["desviacion"] < 1e-9:
            st.info(
                "El campo de viento es nulo. "
                "La trayectoria real coincide con la trayectoria ideal."
            )
        else:
            st.info(
                f"La desviación pasa de **{real['desviacion']:.2f} m** "
                f"a **{corregida['desviacion']:.2f} m** con la corrección."
            )

with tab2:
    st.subheader("Vista superior del recorrido")
    st.caption(
        "Proyección sobre el plano x-y para observar fácilmente la desviación."
    )

    fig2d = go.Figure()

    for datos, nombre, color, dash, ancho in [
        (ideal, "Trayectoria ideal", AZUL, None, 5),
        (real, "Con viento", ROJO, "dash", 4),
        (corregida, "Corregida", DORADO, None, 5),
    ]:
        linea = dict(color=color, width=ancho)
        if dash:
            linea["dash"] = dash

        fig2d.add_trace(
            go.Scatter(
                x=datos["r"][:, 0],
                y=datos["r"][:, 1],
                mode="lines",
                name=nombre,
                line=linea,
            )
        )

    fig2d.add_trace(
        go.Scatter(
            x=[inicio[0]],
            y=[inicio[1]],
            mode="markers+text",
            name="Inicio",
            text=["A · Inicio"],
            textposition="bottom right",
            marker=dict(size=13, color=MORADO),
        )
    )

    fig2d.add_trace(
        go.Scatter(
            x=[destino[0]],
            y=[destino[1]],
            mode="markers+text",
            name="Destino",
            text=["B · Destino"],
            textposition="top left",
            marker=dict(size=14, color=VERDE),
        )
    )

    fig2d.add_trace(
        go.Scatter(
            x=[real["r"][-1, 0]],
            y=[real["r"][-1, 1]],
            mode="markers+text",
            name="Final sin corrección",
            text=["Final sin corrección"],
            textposition="middle right",
            marker=dict(size=11, color=ROJO),
        )
    )

    fig2d.add_trace(
        go.Scatter(
            x=[corregida["r"][-1, 0]],
            y=[corregida["r"][-1, 1]],
            mode="markers+text",
            name="Final corregido",
            text=["Final corregido"],
            textposition="bottom left",
            marker=dict(size=11, color=DORADO),
        )
    )

    fig2d.add_trace(
        go.Scatter(
            x=[destino[0], real["r"][-1, 0]],
            y=[destino[1], real["r"][-1, 1]],
            mode="lines",
            name="Error final",
            line=dict(color=ROJO, width=2, dash="dot"),
            hoverinfo="skip",
        )
    )

    fig2d.update_layout(
        height=620,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="x (m)",
        yaxis_title="y (m)",
        hovermode="closest",
        legend=dict(
            orientation="h",
            y=1.08,
            yanchor="bottom",
            x=0.5,
            xanchor="center",
        ),
    )

    fig2d.update_yaxes(scaleanchor="x", scaleratio=1)

    st.plotly_chart(
        fig2d,
        width="stretch",
        config={"displaylogo": False},
    )

# ==========================================================
# 3D CLIENT-SIDE: FRAMES DE PLOTLY
# ==========================================================

def limites_3d():
    puntos = np.vstack(
        [ideal["r"], real["r"], corregida["r"]]
    )

    mins = puntos.min(axis=0)
    maxs = puntos.max(axis=0)

    amplitud = np.maximum(maxs - mins, 1.0)
    margen = amplitud * 0.12

    return mins - margen, maxs + margen


def crear_figura_3d_animada():
    mins, maxs = limites_3d()

    fig = go.Figure()

    datasets = [
        (ideal, "Ideal", AZUL),
        (real, "Con viento", ROJO),
        (corregida, "Corregida", DORADO),
    ]

    # Las tres trazas se crean desde el comienzo.
    # La leyenda permite ocultar/mostrar con un clic.
    for datos, nombre, color in datasets:
        fig.add_trace(
            go.Scatter3d(
                x=[],
                y=[],
                z=[],
                mode="lines+markers",
                name=nombre,
                line=dict(
                    color=color,
                    width=8,
                ),
                marker=dict(
                    color=color,
                    size=3,
                ),
            )
        )

    # Puntos fijos.
    fig.add_trace(
        go.Scatter3d(
            x=[inicio[0]],
            y=[inicio[1]],
            z=[inicio[2]],
            mode="markers+text",
            name="Inicio",
            text=["A"],
            textposition="top center",
            marker=dict(size=7, color=MORADO),
        )
    )

    fig.add_trace(
        go.Scatter3d(
            x=[destino[0]],
            y=[destino[1]],
            z=[destino[2]],
            mode="markers+text",
            name="Destino",
            text=["B"],
            textposition="top center",
            marker=dict(size=8, color=VERDE),
        )
    )

    # Campo de viento estático y discreto para no recargar.
    indices = np.linspace(
        0,
        len(ideal["r"]) - 1,
        5,
        dtype=int,
    )

    puntos = ideal["r"][indices]

    vectores = np.array(
        [
            campo_viento(
                p,
                rapidez_viento,
                angulo,
                vertical,
                k_altura,
            )
            for p in puntos
        ]
    )

    max_w = float(
        np.max(
            np.linalg.norm(
                vectores,
                axis=1,
            )
        )
    )

    fig.add_trace(
        go.Cone(
            x=puntos[:, 0],
            y=puntos[:, 1],
            z=puntos[:, 2],
            u=vectores[:, 0],
            v=vectores[:, 1],
            w=vectores[:, 2],
            name="Campo de viento",
            showlegend=True,
            visible="legendonly",
            showscale=False,
            opacity=0.32,
            sizemode="absolute",
            sizeref=max(
                2.0,
                max_w * 0.55,
            ),
            anchor="tail",
            colorscale=[
                [0, "#42B6FF"],
                [1, "#B6E3FF"],
            ],
            hovertemplate=(
                "<b>Campo de viento</b><br>"
                "Wx: %{u:.2f} m/s<br>"
                "Wy: %{v:.2f} m/s<br>"
                "Wz: %{w:.2f} m/s"
                "<extra></extra>"
            ),
        )
    )

    # 42 frames es suficiente para que se vea fluido y no sea pesado.
    numero_frames = 42

    indices_frame = np.linspace(
        2,
        len(ideal["r"]),
        numero_frames,
        dtype=int,
    )

    frames = []

    for j, idx in enumerate(indices_frame):
        datos_frame = []

        for datos, nombre, color in datasets:
            datos_frame.append(
                go.Scatter3d(
                    x=datos["r"][:idx, 0],
                    y=datos["r"][:idx, 1],
                    z=datos["r"][:idx, 2],
                    mode="lines+markers",
                    line=dict(color=color, width=8),
                    marker=dict(color=color, size=3),
                )
            )

        frames.append(
            go.Frame(
                data=datos_frame,
                traces=[0, 1, 2],
                name=str(j),
            )
        )

    fig.frames = frames

    frame_ms = 35

    fig.update_layout(
        height=720,
        margin=dict(
            l=0,
            r=0,
            t=85,
            b=10,
        ),
        uirevision="simulacion3d",
        scene=dict(
            bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                title="x (m)",
                range=[mins[0], maxs[0]],
                gridcolor="rgba(255,255,255,.07)",
                showbackground=False,
            ),
            yaxis=dict(
                title="y (m)",
                range=[mins[1], maxs[1]],
                gridcolor="rgba(255,255,255,.07)",
                showbackground=False,
            ),
            zaxis=dict(
                title="z (m)",
                range=[mins[2], maxs[2]],
                gridcolor="rgba(255,255,255,.07)",
                showbackground=False,
            ),
            aspectmode="data",
            camera=dict(
                eye=dict(
                    x=1.45,
                    y=1.55,
                    z=1.20,
                )
            ),
        ),
        legend=dict(
            orientation="h",
            y=1.01,
            yanchor="bottom",
            x=0.5,
            xanchor="center",
            itemclick="toggle",
            itemdoubleclick="toggleothers",
            font=dict(
                size=12,
            ),
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.5,
                xanchor="center",
                y=1.13,
                yanchor="bottom",
                showactive=False,
                pad=dict(
                    t=4,
                    r=8,
                ),
                buttons=[
                    dict(
                        label="▶ Reproducir",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {
                                    "duration": frame_ms,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 0,
                                },
                                "fromcurrent": False,
                                "mode": "immediate",
                            },
                        ],
                    ),
                    dict(
                        label="⏸ Pausar",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": False,
                                },
                                "mode": "immediate",
                            },
                        ],
                    ),
                    dict(
                        label="↺ Reiniciar",
                        method="animate",
                        args=[
                            ["0"],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": True,
                                },
                                "mode": "immediate",
                            },
                        ],
                    ),
                ],
            )
        ],
    )

    return fig


with tab3:
    st.subheader("Simulación dinámica en 3D")

    st.write(
        "Pulsa **Reproducir** para ver cómo se dibujan las trayectorias. "
        "Puedes hacer clic sobre **Ideal**, **Con viento** o **Corregida** "
        "en la leyenda para ocultarlas o mostrarlas. "
        "Con doble clic puedes dejar visible únicamente una."
    )

    st.plotly_chart(
        crear_figura_3d_animada(),
        width="stretch",
        config={
            "displaylogo": False,
            "scrollZoom": True,
        },
    )

    st.caption(
        "El campo de viento aparece inicialmente oculto. "
        "Haz clic en “Campo de viento” en la leyenda si quieres visualizarlo."
    )

with tab4:
    st.subheader("Modelo matemático")

    ca, cb = st.columns(2)

    with ca:
        st.markdown("#### 1 · Posición")
        st.latex(r"\vec r(t)=(x(t),y(t),z(t))")

        st.markdown("#### 2 · Velocidad")
        st.latex(
            r"\vec v(t)=\vec r'(t)"
            r"=(x'(t),y'(t),z'(t))"
        )

        st.markdown("#### 3 · Aceleración")
        st.latex(
            r"\vec a(t)=\vec r''(t)"
            r"=(x''(t),y''(t),z''(t))"
        )

    with cb:
        st.markdown("#### 4 · Campo vectorial del viento")
        st.latex(
            r"\vec W(x,y,z)="
            r"\left(1+\frac{kz}{100}\right)"
            r"\left(w\cos\theta,\;w\sin\theta,\;w_z\right)"
        )

        st.markdown("#### 5 · Movimiento real")
        st.latex(
            r"\frac{d\vec r}{dt}"
            r"=\vec v_D+\vec W(x,y,z)"
        )

        st.markdown("#### 6 · Corrección")
        st.latex(
            r"\vec v_D"
            r"=\vec v_{\mathrm{deseada}}-\vec W"
        )

    st.divider()
    st.subheader("Vectores del escenario actual")
    st.write(
        "A continuación se muestran los vectores principales calculados "
        "en el punto inicial para las condiciones actuales del modelo."
    )

    desplazamiento = destino - inicio
    direccion_unitaria = desplazamiento / np.linalg.norm(desplazamiento)
    vector_dron = rapidez_dron * direccion_unitaria
    vector_viento = campo_viento(
        inicio,
        rapidez_viento,
        angulo,
        vertical,
        k_altura,
    )
    vector_resultante = vector_dron + vector_viento

    tabla_vectores = pd.DataFrame(
        {
            "Vector": [
                "Velocidad propia del dron",
                "Campo de viento",
                "Velocidad resultante",
            ],
            "x (m/s)": [
                vector_dron[0],
                vector_viento[0],
                vector_resultante[0],
            ],
            "y (m/s)": [
                vector_dron[1],
                vector_viento[1],
                vector_resultante[1],
            ],
            "z (m/s)": [
                vector_dron[2],
                vector_viento[2],
                vector_resultante[2],
            ],
            "Norma (m/s)": [
                norma(vector_dron),
                norma(vector_viento),
                norma(vector_resultante),
            ],
        }
    ).round(2)

    st.dataframe(
        tabla_vectores,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Suma vectorial actual")
    st.latex(
        rf"\vec v_D = ({vector_dron[0]:.2f}, {vector_dron[1]:.2f}, "
        rf"{vector_dron[2]:.2f})"
    )
    st.latex(
        rf"\vec W = ({vector_viento[0]:.2f}, {vector_viento[1]:.2f}, "
        rf"{vector_viento[2]:.2f})"
    )
    st.latex(
        rf"\vec v_R = \vec v_D + \vec W = "
        rf"({vector_resultante[0]:.2f}, {vector_resultante[1]:.2f}, "
        rf"{vector_resultante[2]:.2f})"
    )
    st.info(
        "La velocidad resultante corresponde a la suma del vector de "
        "velocidad propio del dron y el vector del viento. Si la magnitud "
        "o dirección del viento cambia, también cambia la velocidad real "
        "y, por tanto, la trayectoria."
    )

    st.divider()

    st.subheader("Método numérico")

    st.write(
        "La ecuación diferencial vectorial se aproxima mediante "
        "Runge-Kutta de cuarto orden (RK4)."
    )

    with st.expander("Ver fórmula"):
        st.latex(
            r"\vec r_{n+1}="
            r"\vec r_n+\frac{\Delta t}{6}"
            r"(k_1+2k_2+2k_3+k_4)"
        )

with tab5:
    st.subheader("Comparación numérica")

    tabla = pd.DataFrame(
        {
            "Escenario": [
                "Ideal",
                "Con viento",
                "Corregido",
            ],
            "Distancia recorrida (m)": [
                round(ideal["distancia"], 2),
                round(real["distancia"], 2),
                round(corregida["distancia"], 2),
            ],
            "Desviación final (m)": [
                0.0,
                round(real["desviacion"], 2),
                round(corregida["desviacion"], 2),
            ],
            "Rapidez media (m/s)": [
                round(rapidez_dron, 2),
                round(real["rapidez_media"], 2),
                round(corregida["rapidez_media"], 2),
            ],
            "Costo J": [
                round(rapidez_dron**2 * ideal["tiempo"], 2),
                round(real["costo"], 2),
                round(corregida["costo"], 2),
            ],
        }
    )

    st.dataframe(
        tabla,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Indicador matemático de esfuerzo")
    st.latex(
        r"""
        J=
        \int_0^T
        \left(
        \|\vec v_D(t)\|^2+
        \lambda\|\vec a(t)\|^2
        \right)dt
        """
    )

    st.caption(
        "En este modelo se utiliza λ = 0.2. El primer término representa "
        "el esfuerzo asociado a mantener la velocidad y el segundo penaliza "
        "cambios de movimiento mediante la aceleración. J es un indicador "
        "matemático comparativo y no representa directamente el consumo "
        "real de batería."
    )

    st.subheader("Interpretación automática")

    if real["desviacion"] < 1e-9:
        texto = (
            "No existe desviación causada por el viento. "
            "Las trayectorias ideal, real y corregida coinciden."
        )
    elif (
        rapidez_viento > rapidez_dron
        and corregida["desviacion"] > 1
    ):
        texto = (
            "La corrección vectorial reduce la desviación, pero el viento "
            "supera la rapidez máxima del dron. Por esta razón, el dron no "
            "logra alcanzar completamente el destino durante el intervalo "
            "de simulación."
        )
    elif mejora > 50:
        texto = (
            "La corrección vectorial reduce de forma importante "
            "la desviación producida por el viento."
        )
    elif mejora > 10:
        texto = (
            "La corrección mejora la trayectoria, aunque todavía "
            "queda una desviación apreciable."
        )
    else:
        texto = (
            "La capacidad de corrección es limitada para las "
            "condiciones seleccionadas."
        )

    st.success(texto)

    if real["desviacion"] < 1e-9:
        st.write(
            "Como el campo de viento es nulo, no existe "
            "desviación que deba ser corregida."
        )
    else:
        st.write(
            f"La desviación cambia de **{real['desviacion']:.2f} m** a "
            f"**{corregida['desviacion']:.2f} m**, equivalente a una reducción "
            f"aproximada del **{mejora:.1f} %**."
        )

    st.caption(
        "Las tablas y métricas se recalculan automáticamente "
        "al cambiar cualquier coordenada o parámetro."
    )

st.divider()
st.caption(
    "Proyecto académico · Cálculo Multivariado · Ingeniería de Sistemas · CUN"
)
