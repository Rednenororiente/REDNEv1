# -*- coding: utf-8 -*-
"""Untitled34.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1uWzrVZny02KjyV-dksZKIxUF3pKG9Cag
"""
from flask import Flask, request, send_file, jsonify
from obspy import read
import requests
import io
import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Para evitar problemas de GUI en entornos sin pantalla

app = Flask(__name__)

# Función auxiliar para calcular la diferencia de tiempo
def calculate_time_difference(start, end):
    start_time = datetime.datetime.fromisoformat(start)
    end_time = datetime.datetime.fromisoformat(end)
    return (end_time - start_time).total_seconds() / 60  # Diferencia en minutos

# Ruta para generar sismograma o helicorder dinámicamente
@app.route('/generate_graph', methods=['GET'])
def generate_graph():
    try:
        # Obtener parámetros de la solicitud
        start = request.args.get('start')
        end = request.args.get('end')
        net = request.args.get('net')
        sta = request.args.get('sta')
        loc = request.args.get('loc')
        cha = request.args.get('cha')

        # Verificar que todos los parámetros estén presentes
        if not all([start, end, net, sta, loc, cha]):
            return jsonify({"error": "Faltan parámetros requeridos"}), 400

        # Calcular la diferencia de tiempo para decidir el tipo de gráfico
        interval_minutes = calculate_time_difference(start, end)
        if interval_minutes <= 30:
            return generate_sismograma(net, sta, loc, cha, start, end)
        else:
            return generate_helicorder(net, sta, loc, cha, start, end)

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Función para generar sismograma
def generate_sismograma(net, sta, loc, cha, start, end):
    try:
        # Construir la URL para descargar datos desde `osso.univalle.edu.co`
        url = f"http://osso.univalle.edu.co/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"

        # Solicitar los datos MiniSEED
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Procesar los datos MiniSEED
        mini_seed_data = io.BytesIO(response.content)
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando MiniSEED: {str(e)}"}), 500

        # Crear gráfico del sismograma
        tr = st[0]
        start_time = tr.stats.starttime.datetime
        times = [start_time + datetime.timedelta(seconds=sec) for sec in tr.times()]
        data = tr.data

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(times, data, color='black', linewidth=0.8)
        ax.set_title(f"{start} - {end}")
        ax.set_xlabel("Tiempo")
        ax.set_ylabel("Amplitud")
        fig.autofmt_xdate()

        # Guardar el gráfico en memoria
        output_image = io.BytesIO()
        plt.savefig(output_image, format='png', dpi=120, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Función para generar helicorder
def generate_helicorder(net, sta, loc, cha, start, end):
    try:
        # Construir la URL para descargar datos desde `osso.univalle.edu.co`
        url = f"http://osso.univalle.edu.co/fdsnws/dataselect/1/query?starttime={start}&endtime={end}&network={net}&station={sta}&location={loc}&channel={cha}&nodata=404"

        # Solicitar los datos MiniSEED
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": f"Error al descargar datos: {response.status_code}"}), 500

        # Procesar los datos MiniSEED
        mini_seed_data = io.BytesIO(response.content)
        try:
            st = read(mini_seed_data)
        except Exception as e:
            return jsonify({"error": f"Error procesando MiniSEED: {str(e)}"}), 500

        # Crear helicorder
        fig = st.plot(
            type="dayplot",
            interval=30,
            right_vertical_labels=True,
            vertical_scaling_range=2000,
            color=['k', 'r', 'b'],
            show_y_UTC_label=True,
            one_tick_per_line=True
        )

        # Guardar el gráfico en memoria
        output_image = io.BytesIO()
        fig.savefig(output_image, format='png', dpi=150, bbox_inches="tight")
        output_image.seek(0)
        plt.close(fig)

        return send_file(output_image, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": f"Ocurrió un error: {str(e)}"}), 500

# Punto de entrada para el servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
