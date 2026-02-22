def print_ticket(producto):
    try:
        import win32print
    except ImportError:
        raise RuntimeError("Impresión solo disponible en Windows")

    PRINTER_NAME = "Xprinter XP-58"
    ...
