import random
import streamlit as st

st.set_page_config(page_title="Trivia: Villanas de Disney", page_icon="🍎", layout="centered")

# ---------------------------------------------------------------------------
# Preguntas (la primera alternativa de cada lista es la correcta;
# el orden que ve el usuario se baraja al iniciar cada partida)
# ---------------------------------------------------------------------------
PREGUNTAS = [
    {
        "pregunta": "¿Qué villana le quita la voz a Ariel a cambio de darle piernas humanas?",
        "opciones": ["Úrsula", "Maléfica", "Madre Gothel", "Lady Tremaine"],
    },
    {
        "pregunta": "¿Cómo se llama el cuervo que acompaña a Maléfica en La Bella Durmiente?",
        "opciones": ["Diablo", "Lucifer", "Flotsam", "Iago"],
    },
    {
        "pregunta": "¿Qué villana quiere un abrigo hecho con la piel de los cachorros dálmatas?",
        "opciones": ["Cruella de Vil", "Úrsula", "La Reina de Corazones", "Madame Medusa"],
    },
    {
        "pregunta": "En Blancanieves, ¿a quién le pregunta la Reina Malvada quién es la más bella del reino?",
        "opciones": ["A su espejo mágico", "A su cuervo", "A un caldero encantado", "A una bola de cristal"],
    },
    {
        "pregunta": "¿Por qué la Madre Gothel mantiene encerrada a Rapunzel en la torre?",
        "opciones": [
            "Porque su cabello la mantiene joven",
            "Porque Rapunzel es heredera de su trono",
            "Porque le robó una corona",
            "Porque es la hija de su enemiga",
        ],
    },
]


# ---------------------------------------------------------------------------
# Estado de la partida
# ---------------------------------------------------------------------------
def nueva_partida():
    preguntas = []
    for p in random.sample(PREGUNTAS, k=len(PREGUNTAS)):  # orden de preguntas aleatorio
        opciones = p["opciones"][:]
        random.shuffle(opciones)                           # orden de alternativas aleatorio
        preguntas.append({"pregunta": p["pregunta"], "opciones": opciones, "correcta": p["opciones"][0]})
    st.session_state.preguntas = preguntas
    st.session_state.enviado = False
    st.session_state.ronda = st.session_state.get("ronda", 0) + 1  # renueva las claves de los radios


if "preguntas" not in st.session_state:
    nueva_partida()

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Grenze+Gotisch:wght@500;700&family=Crimson+Pro:wght@400;600&display=swap');

    .stApp { background: radial-gradient(circle at 50% 0%, #3B1F4F 0%, #1E0F2E 60%); }
    html, body, [class*="css"], .stMarkdown, .stRadio label { font-family: 'Crimson Pro', Georgia, serif; }

    h1.titulo {
        font-family: 'Grenze Gotisch', 'Times New Roman', serif;
        font-size: clamp(2.6rem, 8vw, 4.2rem);
        color: #E8C872;
        text-align: center;
        line-height: 1;
        margin-bottom: .25rem;
        text-shadow: 0 0 18px rgba(127, 211, 91, .45);
    }
    p.subtitulo { text-align: center; color: #CDB8DA; font-size: 1.15rem; margin-bottom: 2rem; }

    .pregunta {
        font-family: 'Grenze Gotisch', serif;
        font-size: 1.5rem;
        color: #F2E9F7;
        border-left: 3px solid #7FD35B;
        padding-left: .8rem;
        margin: 1.6rem 0 .4rem;
    }
    .ok  { color: #7FD35B; font-size: 1.05rem; }
    .mal { color: #F28B8B; font-size: 1.05rem; }

    /* Animación de victoria: coronas y manzanas que caen */
    .lluvia { position: fixed; inset: 0; pointer-events: none; overflow: hidden; z-index: 9999; }
    .lluvia span {
        position: absolute; top: -3rem; font-size: 2rem;
        animation: caer linear forwards;
    }
    @keyframes caer {
        to { transform: translateY(110vh) rotate(540deg); opacity: .2; }
    }
    .victoria {
        text-align: center; font-family: 'Grenze Gotisch', serif; color: #E8C872;
        font-size: clamp(2rem, 6vw, 3rem);
        animation: pulso 1.2s ease-in-out infinite alternate;
    }
    @keyframes pulso {
        from { transform: scale(1);    text-shadow: 0 0 10px #7FD35B; }
        to   { transform: scale(1.08); text-shadow: 0 0 30px #7FD35B; }
    }
    @media (prefers-reduced-motion: reduce) {
        .lluvia { display: none; }
        .victoria { animation: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="titulo">Villanas de Disney</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitulo">Cinco preguntas. Acierta todas y el reino será tuyo.</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Preguntas
# ---------------------------------------------------------------------------
respuestas = []
for i, p in enumerate(st.session_state.preguntas):
    st.markdown(f'<div class="pregunta">{i + 1}. {p["pregunta"]}</div>', unsafe_allow_html=True)
    r = st.radio(
        label=p["pregunta"],
        options=p["opciones"],
        index=None,
        key=f"r{st.session_state.ronda}_{i}",
        label_visibility="collapsed",
        disabled=st.session_state.enviado,
    )
    respuestas.append(r)

    if st.session_state.enviado:
        if r == p["correcta"]:
            st.markdown('<p class="ok">✔ Correcto</p>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<p class="mal">✘ La respuesta era: {p["correcta"]}</p>', unsafe_allow_html=True
            )

st.write("")

# ---------------------------------------------------------------------------
# Envío y resultado
# ---------------------------------------------------------------------------
if not st.session_state.enviado:
    if st.button("Ver mi resultado", type="primary", use_container_width=True):
        if None in respuestas:
            st.warning("Responde las cinco preguntas antes de ver tu resultado.")
        else:
            st.session_state.enviado = True
            st.rerun()
else:
    aciertos = sum(r == p["correcta"] for r, p in zip(respuestas, st.session_state.preguntas))
    total = len(st.session_state.preguntas)

    if aciertos == total:
        st.balloons()
        emojis = ["👑", "🍎", "✨", "🔮", "🐍"]
        gotas = "".join(
            f'<span style="left:{random.randint(0, 95)}vw;'
            f'animation-duration:{random.uniform(2.5, 5):.2f}s;'
            f'animation-delay:{random.uniform(0, 1.5):.2f}s">{random.choice(emojis)}</span>'
            for _ in range(40)
        )
        st.markdown(f'<div class="lluvia">{gotas}</div>', unsafe_allow_html=True)
        st.markdown('<p class="victoria">¡5 de 5! Eres la reina de las villanas 👑</p>', unsafe_allow_html=True)
    else:
        st.info(f"Acertaste {aciertos} de {total}. ¡Inténtalo otra vez para desbloquear la sorpresa!")

    if st.button("Jugar de nuevo", use_container_width=True):
        nueva_partida()
        st.rerun()
