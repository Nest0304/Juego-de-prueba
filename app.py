import random

import joblib
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from entrenar_modelo import URL, entrenar, preparar

st.set_page_config(page_title="¿Habrías sobrevivido al Titanic?", page_icon="🚢", layout="centered")

FEATURES = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "FamilySize", "IsAlone", "Emb_Q", "Emb_S"]
PUERTOS = {"Southampton (Inglaterra)": "S", "Cherbourg (Francia)": "C", "Queenstown (Irlanda)": "Q"}
TARIFA_TIPICA = {1: 60.0, 2: 14.0, 3: 8.0}  # mediana aproximada de Fare por clase


# ---------------------------------------------------------------------------
# Carga de datos y modelo
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Cargando datos del Titanic...")
def cargar_datos():
    return pd.read_csv(URL)


@st.cache_resource(show_spinner="Cargando el modelo...")
def cargar_modelo():
    df = cargar_datos()
    _, X_train, X_test, y_train, y_test = entrenar(df)
    try:
        model = joblib.load("random_forest_titanic.pkl")
        origen = "Modelo cargado desde random_forest_titanic.pkl"
    except Exception:
        # Si el .pkl falta o no es compatible con la versión de scikit-learn, se reentrena igual que en el notebook
        model, *_ = entrenar(df)
        origen = "Modelo reentrenado al iniciar (no se pudo cargar el .pkl)"
    return model, X_test, y_test, origen


df_raw = cargar_datos()
model, X_test, y_test, origen_modelo = cargar_modelo()


def construir_fila(pclass, sexo, edad, sibsp, parch, fare, puerto):
    familia = sibsp + parch + 1
    return pd.DataFrame([{
        "Pclass": pclass,
        "Sex": 1 if sexo == "Mujer" else 0,
        "Age": edad,
        "SibSp": sibsp,
        "Parch": parch,
        "Fare": fare,
        "FamilySize": familia,
        "IsAlone": int(familia == 1),
        "Emb_Q": int(puerto == "Q"),
        "Emb_S": int(puerto == "S"),
    }])[FEATURES]


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------
st.title("🚢 ¿Habrías sobrevivido al Titanic?")
st.write(
    "Un modelo **Random Forest** entrenado con los 891 pasajeros del Titanic estima la probabilidad "
    "de supervivencia a partir de los datos que ingreses."
)

tab_pred, tab_validar, tab_metricas = st.tabs(["Predecir", "Validar con pasajeros reales", "Métricas del modelo"])

# ---------------- Pestaña 1: el usuario ingresa datos ----------------
with tab_pred:
    st.subheader("Ingresa los datos del pasajero")

    col1, col2 = st.columns(2)
    with col1:
        sexo = st.radio("Sexo", ["Mujer", "Hombre"], horizontal=True)
        edad = st.slider("Edad", 0, 80, 28)
        pclass = st.selectbox(
            "Clase del pasaje", [1, 2, 3], index=2,
            format_func=lambda c: {1: "1ra clase", 2: "2da clase", 3: "3ra clase"}[c],
        )
    with col2:
        sibsp = st.number_input("Hermanos o cónyuge a bordo", 0, 8, 0)
        parch = st.number_input("Padres o hijos a bordo", 0, 6, 0)
        puerto_nombre = st.selectbox("Puerto de embarque", list(PUERTOS))

    fare = st.number_input(
        "Tarifa pagada (libras de 1912)", min_value=0.0, max_value=520.0,
        value=TARIFA_TIPICA[pclass], step=1.0,
        help="Se propone la tarifa típica de la clase elegida; puedes cambiarla.",
    )

    if st.button("Predecir supervivencia", type="primary", use_container_width=True):
        fila = construir_fila(pclass, sexo, edad, sibsp, parch, fare, PUERTOS[puerto_nombre])
        proba = model.predict_proba(fila)[0, 1]

        st.divider()
        if proba >= 0.5:
            st.success(f"### Sobrevive 🛟  \nProbabilidad estimada: **{proba:.0%}**")
        else:
            st.error(f"### No sobrevive 🌊  \nProbabilidad estimada: **{proba:.0%}**")
        st.progress(float(proba))

        # Comparación con pasajeros reales parecidos
        similares = df_raw[(df_raw["Pclass"] == pclass) & (df_raw["Sex"] == ("female" if sexo == "Mujer" else "male"))]
        if len(similares):
            st.caption(
                f"Como referencia, de los {len(similares)} pasajeros reales del mismo sexo y clase, "
                f"sobrevivió el {similares['Survived'].mean():.0%}."
            )
        with st.expander("Ver los datos que recibió el modelo"):
            st.dataframe(fila, hide_index=True)

# ---------------- Pestaña 2: validación con el conjunto de prueba ----------------
with tab_validar:
    st.subheader("Pon a prueba al modelo")
    st.write(
        "Se elige un pasajero real del **conjunto de prueba** (datos que el modelo no vio al entrenar). "
        "Primero adivina tú, luego compara con el modelo y con lo que pasó en realidad."
    )

    if "marcador" not in st.session_state:
        st.session_state.marcador = {"usuario": 0, "modelo": 0, "total": 0}
    if "idx" not in st.session_state:
        st.session_state.idx = random.choice(list(X_test.index))
        st.session_state.revelado = False

    idx = st.session_state.idx
    p = df_raw.loc[idx]
    st.markdown(
        f"**{p['Name']}**  \n"
        f"{'Mujer' if p['Sex'] == 'female' else 'Hombre'}, "
        f"{'edad desconocida' if pd.isna(p['Age']) else f'{int(p.Age)} años'}, "
        f"{int(p['Pclass'])}ª clase, tarifa £{p['Fare']:.2f}, "
        f"{int(p['SibSp'])} hermanos/cónyuge y {int(p['Parch'])} padres/hijos a bordo."
    )

    guess = st.radio("¿Crees que sobrevivió?", ["Sí", "No"], horizontal=True, index=None,
                     key=f"guess_{idx}", disabled=st.session_state.revelado)

    c1, c2 = st.columns(2)
    if c1.button("Revelar resultado", disabled=guess is None or st.session_state.revelado, use_container_width=True):
        real = int(y_test.loc[idx])
        pred = int(model.predict(X_test.loc[[idx]])[0])
        m = st.session_state.marcador
        m["total"] += 1
        m["usuario"] += int((guess == "Sí") == bool(real))
        m["modelo"] += int(pred == real)
        st.session_state.revelado = True
        st.session_state.ultimo = (real, pred, model.predict_proba(X_test.loc[[idx]])[0, 1])
        st.rerun()

    if c2.button("Otro pasajero", use_container_width=True):
        st.session_state.idx = random.choice(list(X_test.index))
        st.session_state.revelado = False
        st.rerun()

    if st.session_state.revelado:
        real, pred, proba = st.session_state.ultimo
        txt = lambda v: "sobrevivió" if v else "no sobrevivió"
        st.info(f"En la realidad, este pasajero **{txt(real)}**.")
        (st.success if pred == real else st.warning)(
            f"El modelo predijo que {txt(pred)} (probabilidad {proba:.0%}): "
            f"{'acertó ✔' if pred == real else 'se equivocó ✘'}"
        )

    m = st.session_state.marcador
    if m["total"]:
        a, b = st.columns(2)
        a.metric("Tus aciertos", f"{m['usuario']} / {m['total']}")
        b.metric("Aciertos del modelo", f"{m['modelo']} / {m['total']}")

# ---------------- Pestaña 3: métricas ----------------
with tab_metricas:
    st.subheader("Rendimiento en el conjunto de prueba (20%)")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    c1, c2, c3 = st.columns(3)
    c1.metric("Accuracy", f"{accuracy_score(y_test, y_pred):.3f}")
    c2.metric("Precision", f"{precision_score(y_test, y_pred):.3f}")
    c3.metric("Recall", f"{recall_score(y_test, y_pred):.3f}")
    c4, c5, _ = st.columns(3)
    c4.metric("F1-score", f"{f1_score(y_test, y_pred):.3f}")
    c5.metric("ROC-AUC", f"{roc_auc_score(y_test, y_proba):.3f}")

    st.markdown("**Matriz de confusión**")
    cm = confusion_matrix(y_test, y_pred)
    st.dataframe(
        pd.DataFrame(cm, index=["Real: no sobrevivió", "Real: sobrevivió"],
                     columns=["Predicho: no sobrevivió", "Predicho: sobrevivió"])
    )

    st.markdown("**Importancia de variables**")
    st.bar_chart(pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False))
    st.caption(origen_modelo)
