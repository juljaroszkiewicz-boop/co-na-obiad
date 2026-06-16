import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import random

# Konfiguracja strony
st.set_page_config(
    page_title="Co na obiad?",
    page_icon="🎲",
    layout="centered"
)

PEOPLE = ['Ewa', 'Robert', 'Mateusz', 'Julia']

st.title("🎲 Co dzisiaj jemy?")
st.write("Aplikacja w chmurze zsynchronizowana z Arkuszem Google.")

# Nawiązanie połączenia z Google Sheets (Streamlit automatycznie pobierze dane logowania z tzw. Secrets)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl="1m")  # Odświeżaj dane z arkusza co 1 minutę
except Exception as e:
    st.error("Brak połączenia z bazą danych (Arkuszem Google). Skonfiguruj Secrets w panelu Streamlit.")
    df = pd.DataFrame(columns=["Nazwa", "Zdjecie", "Osoba 1", "Osoba 2", "Osoba 3", "Osoba 4"])

# Zakładki menu
tab_draw, tab_manage = st.tabs(["✨ Losowanie", "⚙️ Zarządzaj daniami"])

# ================= ZAKŁADKA 1: LOSOWANIE =================
with tab_draw:
    st.subheader("Kto dzisiaj je obiad?")

    selected_people = []
    cols = st.columns(4)
    for i, person in enumerate(PEOPLE):
        with cols[i]:
            if st.checkbox(person, value=True, key=f"draw_{person}"):
                selected_people.append(person)

    st.markdown("---")

    if st.button("🎲 LOSUJ OBIAD", type="primary", use_container_width=True):
        if not selected_people:
            st.warning("⚠️ Zaznacz przynajmniej jedną osobę!")
        elif df.empty:
            st.error("😭 Baza dań jest pusta! Dodaj potrawy w zakładce obok.")
        else:
            # Filtrowanie dań na podstawie tabeli z Arkusza
            valid_dishes = []

            for index, row in df.iterrows():
                # Sprawdzamy czy każda z zaznaczonych osób ma wartość TRUE (lub 1) w arkuszu dla tego dania
                all_eat = True
                for person in selected_people:
                    if not row.get(person) or str(row[person]).upper() not in ["TRUE", "1", "TAK"]:
                        all_eat = False
                        break
                if all_eat:
                    valid_dishes.append(row)

            if not valid_dishes:
                st.error("😭 Brak dań, które smakują WSZYSTKIM zaznaczonym osobom!")
            else:
                drawn_row = random.choice(valid_dishes)
                drawn_name = drawn_row["Nazwa"]
                img_url = drawn_row.get("Zdjecie", "")

                st.balloons()
                st.success(f"### 🎉 Wylosowano danie:\n## **{drawn_name}**")

                # Wyświetlanie zdjęcia za pomocą linku URL
                if pd.notna(img_url) and str(img_url).strip().startswith(("http://", "https://")):
                    st.image(img_url, caption=f"Pyszny {drawn_name}", use_container_width=True)
                else:
                    st.info("ℹ️ To danie nie ma przypisanego poprawnego linku do zdjęcia.")

# ================= ZAKŁADKA 2: ZARZĄDZANIE =================
with tab_manage:
    st.subheader("Zarządzanie bazą potraw")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### ➕ Dodaj danie")
        new_name = st.text_input("Nazwa potrawy:", placeholder="np. Pierogi ruskie")

        # W chmurze najbezpieczniej podawać bezpośredni link do zdjęcia z internetu
        # (np. z Imgura, Pinteresta lub dowolnego bloga kulinTargetu)
        new_img_url = st.text_input("Link URL do zdjęcia potrawy (opcjonalnie):",
                                    placeholder="https://example.com/zdjecie.jpg")

        st.write("Kto jada to danie?")
        preferences = {}
        for person in PEOPLE:
            preferences[person] = st.checkbox(person, value=True, key=f"manage_{person}")

        if st.button("💾 Zapisz potrawę", use_container_width=True):
            if not new_name.strip():
                st.error("❌ Podaj nazwę potrawy!")
            else:
                # Przygotowanie nowego wiersza do dopisania
                new_row = {
                    "Nazwa": new_name.strip(),
                    "Zdjecie": new_img_url.strip(),
                }
                for person in PEOPLE:
                    new_row[person] = "TRUE" if preferences[person] else "FALSE"

                # Dodanie wiersza do aktualnego DataFrame i wysłanie do Google Sheets
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"✔️ Dodano i zsynchronizowano danie: {new_name}")
                st.rerun()

    with col_right:
        st.markdown("### 📋 Zapisane potrawy")
        if df.empty:
            st.write("Baza dań w Arkuszu Google jest pusta.")
        else:
            for index, row in df.iterrows():
                dish_name = row["Nazwa"]
                dish_cols = st.columns([3, 1])
                with dish_cols[0]:
                    # Wyświetlamy kto je to danie
                    kto_je = [p for p in PEOPLE if str(row.get(p)).upper() in ["TRUE", "1", "TAK"]]
                    st.write(f"**{dish_name}** \n_(Jada: {', '.join(kto_je)})_")
                with dish_cols[1]:
                    if st.button("🗑️", key=f"del_{index}"):
                        # Usunięcie wiersza i aktualizacja w Google Sheets
                        updated_df = df.drop(index)
                        conn.update(data=updated_df)
                        st.toast(f"Usunięto {dish_name}")
                        st.rerun()