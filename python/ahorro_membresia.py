# ahorro_membresia.py
# Simulador de ahorro con la membresía UVC

def pedir_float(mensaje, valor_default=None):
    """
    Pide un número flotante por consola.
    Si el usuario deja vacío y hay default, regresa el default.
    """
    while True:
        texto = input(mensaje).strip()
        if texto == "" and valor_default is not None:
            return valor_default
        try:
            return float(texto)
        except ValueError:
            print("Por favor escribe un número válido.\n")


def simulador_ahorro():
    print("=" * 60)
    print("  SIMULADOR DE AHORRO – UNLIMITED VACATION CLUB")
    print("=" * 60)

    # --- Datos básicos del cliente / oferta ---
    costo_membresia = pedir_float(
        "\n¿Cuánto cuesta la membresía en USD? (ej. 6500): "
    )

    precio_retail = pedir_float(
        "¿Cuánto pagaría HOY el cliente por estas vacaciones en retail (USD)? "
        "\n   Ejemplo: 5000  → "
    )

    precio_mayoreo = pedir_float(
        "¿Cuál sería el precio con membresía para el MISMO viaje (USD)? "
        "\n   Ejemplo: 2500  → "
    )

    viajes_por_anio = pedir_float(
        "¿Cuántos viajes similares hace al año esta familia? (ej. 1.5): "
    )

    anios = int(
        pedir_float("¿Cuántos años quieres simular? (ej. 5): ")
    )

    inflacion = pedir_float(
        "Inflación anual estimada en precios RETAIL (%) [Enter = 0]: ",
        valor_default=0.0
    ) / 100.0

    print("\nCalculando escenario...\n")

    # --- Cálculo ---
    acumulado_retail = 0.0
    acumulado_membresia = costo_membresia  # se paga al inicio

    anio_quiebre = None  # año en que la membresía se paga sola

    filas = []
    for anio in range(1, anios + 1):
        # El retail sube cada año por inflación
        precio_retail_anio = precio_retail * ((1 + inflacion) ** (anio - 1))

        # El precio con membresía lo dejamos fijo
        precio_mayoreo_anio = precio_mayoreo

        gasto_retail_anio = precio_retail_anio * viajes_por_anio
        gasto_membresia_anio = precio_mayoreo_anio * viajes_por_anio

        acumulado_retail += gasto_retail_anio
        acumulado_membresia += gasto_membresia_anio

        ahorro_acumulado = acumulado_retail - acumulado_membresia

        if anio_quiebre is None and ahorro_acumulado >= 0:
            anio_quiebre = anio

        filas.append({
            "anio": anio,
            "precio_retail": precio_retail_anio,
            "precio_mayoreo": precio_mayoreo_anio,
            "gasto_retail": gasto_retail_anio,
            "gasto_membresia": gasto_membresia_anio,
            "acum_retail": acumulado_retail,
            "acum_membresia": acumulado_membresia,
            "ahorro": ahorro_acumulado,
        })

    # --- Mostrar tabla resumen ---
    print("=" * 90)
    print(
        f"{'Año':<4} {'Retail/año':>13} {'UVC/año':>13} "
        f"{'Acum retail':>13} {'Acum UVC':>13} {'Ahorro acumulado':>18}"
    )
    print("-" * 90)

    for f in filas:
        print(
            f"{f['anio']:<4} "
            f"{f['gasto_retail']:>13.0f} "
            f"{f['gasto_membresia']:>13.0f} "
            f"{f['acum_retail']:>13.0f} "
            f"{f['acum_membresia']:>13.0f} "
            f"{f['ahorro']:>18.0f}"
        )

    print("=" * 90)
    print(f"Total sin membresía (retail):  USD {acumulado_retail:,.0f}")
    print(f"Total con membresía (UVC):      USD {acumulado_membresia:,.0f}")
    print(f"Ahorro total en {anios} años:    USD {acumulado_retail - acumulado_membresia:,.0f}")

    if anio_quiebre:
        print(
            f"\n💡 La membresía se 'paga sola' alrededor del AÑO {anio_quiebre} "
            f"(a partir de ahí todo es ahorro puro)."
        )
    else:
        print(
            "\n⚠️ Con estos números, en el periodo simulado la membresía aún no se paga sola.\n"
            "   (Prueba con más años, más viajes o mayor diferencia entre retail y mayoreo.)"
        )

    print("\nSimulación terminada.\n")


if __name__ == "__main__":
    simulador_ahorro()
