import numpy as np
import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go


def get_current_temperature(city, api_key):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"

    response = requests.get(url)

    data = response.json()

    if response.status_code == 200:
        return data["main"]["temp"]
    else:
        return response.json()


def get_season_temperature(df, city, season):
    historical_temperature = df.groupby(["city", "season"]).get_group((city, season))["temperature"]
    return historical_temperature


def is_anomaly(df, city, season):
    season_temperature = get_season_temperature(df, city, season)

    mean = np.mean(season_temperature)
    std = np.std(season_temperature)

    lower_bound = mean - std
    upper_bound = mean + std

    city_current_temperature = get_current_temperature(city, api_key)

    is_anomaly = ((city_current_temperature < lower_bound) | (city_current_temperature > upper_bound))

    result = "Да" if is_anomaly else "Нет"

    return f"Является ли аномалией нынешняя температура в городе {city}?\nОтвет: {result}"


def show_statistic_information(df, selected_city, year):
    df_city = df[df["city"] == selected_city]

    min_temperature = df_city["temperature"].min()
    max_temperature = df_city["temperature"].max()

    min_temperature_date = df_city[df_city["temperature"] == min_temperature]["timestamp"].values[0]
    max_temperature_date = df_city[df_city["temperature"] == max_temperature]["timestamp"].values[0]

    mean_temperature_spring = df_city[df_city["season"] == "spring"]["temperature"].mean()

    count_days_with_temperature_above_zero = len(df_city[(df_city["temperature"] < 0) & (df["timestamp"].str.contains(year))])
    count_days_with_temperature_below_zero = len(df_city[(df_city["temperature"] > 0) & (df["timestamp"].str.contains(year))])

    st.markdown(f"Минимальная температура: {min_temperature}°C (дата: {min_temperature_date})")
    st.markdown(f"Максимальная температура: {max_temperature}°C (дата: {max_temperature_date})")

    st.markdown(f"Средняя температура весной: {mean_temperature_spring}°C")

    st.markdown(f"Количество дней с температурой выше нуля за {year} год: {count_days_with_temperature_above_zero}")
    st.markdown(f"Количество дней с температурой ниже нуля за {year} год: {count_days_with_temperature_below_zero}")



def show_temperature_plot(df, city, season, year):
    df_city_season = df[(df["city"] == city) & (df["season"] == season) & (df["timestamp"].str.contains(year))]

    season_temperature = get_season_temperature(df, city, season)

    mean = np.mean(season_temperature)
    std = np.std(season_temperature)
    lower_bound = mean - std
    upper_bound = mean + std

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_city_season["timestamp"], y=df_city_season["temperature"], mode='lines', name='Температура'))
    fig.add_trace(go.Scatter(x=df_city_season["timestamp"], y=[mean] * len(df_city_season), mode='lines', name='Среднее', line=dict(color='blue', dash='dash')))
    fig.add_trace(go.Scatter(x=df_city_season["timestamp"], y=[lower_bound] * len(df_city_season), mode='lines', name='Нижнее отклонение', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=df_city_season["timestamp"], y=[upper_bound] * len(df_city_season), mode='lines', name='Верхнее отклонение', line=dict(color='red')))
    fig.update_layout(title=f"Температура в {city} за {season} {year} года", xaxis_title="Дата", yaxis_title="Температура", xaxis=dict(tickangle=-45))
    st.plotly_chart(fig)


def show_season_profiles(df, city):
    df_city = df[df["city"] == city]
    seasonal_profiles = df_city.groupby("season")["temperature"].agg([np.mean, np.std]).reset_index()
    fig = px.bar(seasonal_profiles, x="season", y="mean", error_y="std", title=f"Сезонный профиль температуры в {city}", labels={"mean": "Средняя температура", "season": "Сезон"})
    st.plotly_chart(fig)


# Код самого приложения
st.title("Температура в разных городах")

file = st.file_uploader("Выберите CSV-файл", type="csv")

if file is not None:
    df = pd.read_csv(file)
    st.write(df)

    cities = list(df["city"].unique())

    selected_city = st.selectbox('Выберите город:', cities)
    current_season = "spring"
    year = "2019"

    st.write(f'Вы выбрали: {selected_city}')

    api_key = st.text_input("Введите ключ API-ключ OpenWeatherMap")

    if st.button("Отправить"):
        current_temperature = get_current_temperature(selected_city, api_key)
        if type(current_temperature) is float:
            st.markdown(f"Сейчас температура в городе {selected_city} равна {current_temperature}.")
            st.markdown(is_anomaly(df, selected_city, current_season))
            show_statistic_information(df, selected_city, year)
            show_temperature_plot(df, selected_city, current_season, year)
            show_season_profiles(df, selected_city)
        else:
            st.markdown(current_temperature)
