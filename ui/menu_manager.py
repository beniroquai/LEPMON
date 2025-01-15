
class MenuManager:
    """
    Handle the states of your on-device menu, e.g. focus, GPS input, time setup, etc.
    This class can use the OLEDDisplay and ButtonInput classes to guide the user.
    """
    def __init__(self, display, buttons):
        self.display = display
        self.buttons = buttons  # dictionary of all relevant buttons

    def show_main_menu(self):
        self.display.show_message(["Menü:", "1) Fokus", "2) Uhrzeit", "3) Koordinaten"])
        # then wait for user input on the buttons and navigate
