from libqtile.widget import base
from libqtile import bar, images
from libqtile.log_utils import logger

from .footballscores import FootballMatch


class LiveFootballScoresWidget(base._Widget, base.MarginMixin):

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size"),
        ("font_colour", "ffffff", "Text colour"),
        ("team", "Chelsea", "Team whose scores you want to display"),
        ("status_text", "{H:.3} {h}-{a} {A:.3}", "Default widget match text"),
        ("info_text",
            ["{T}",
             "{H:.3}: {G:10}",
             "{A:.3}: {g:10}",
             "{C}"],
            """Add extra text lines which can be displayed by clicking on widget.
            Available fields are:
             {H}: Home Team name
             {A}: Away Team name
             {h}: Home score
             {a}: Away score
             {C}: Competition
             {v}: Venue
             {T}: Display time (kick-off, elapsed time, HT, FT)
             {S}: Status (as above but no elapsed time)
             {G}: Home goalscorers
             {g}: Away goalscorers
             {R}: Home red cards
             {r}: Away red cards"""
        ),
        ("refresh_interval", 60, "Time to update data"),
        ("info_timeout", 5, "Time before reverting to default text")
    ]

    def __init__(self, **config):
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(LiveFootballScoresWidget.defaults)
        self.add_defaults(base.MarginMixin.defaults)

        # Create foorball match object
        self.match = FootballMatch(self.team, detailed=True)

        # Define our screens
        self.screens = [self.status_text] + self.info_text
        self.screen_index = 0

        # Initial variables to hide text
        self.show_text = False
        self.default_timer = None
        self.refresh_timer = None

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)
        self.set_refresh_timer()
        self.update()

    def set_refresh_timer(self):
        self.refresh_timer = self.timeout_add(self.refresh_interval,
                                              self.refresh)

    def refresh(self):
        self.match.update()
        self.set_refresh_timer()
        self.update()

    def calculate_length(self):

        if self.match:
            screen = self.screens[self.screen_index]
            text = self.match.formatText(screen)
        else:
            text = ""

        width, _ = self.drawer.max_layout_size(
            [text],
            self.font,
            self.fontsize
        )

        return width + 2 * self.margin

    def update(self):
        # Remove background
        self.drawer.clear(self.background or self.bar.background)

        if self.match:
            screen = self.screens[self.screen_index]
            text = self.match.formatText(screen)
        else:
            text = ""

        # Create a text box
        layout = self.drawer.textlayout(text,
                                        self.font_colour,
                                        self.font,
                                        self.fontsize,
                                        None,
                                        wrap=False)

        # We want to centre this vertically
        y_offset = (self.bar.height - layout.height) / 2

        # Draw it
        layout.draw(self.margin_x, y_offset)

        # Redraw the bar
        self.bar.draw()

    def draw(self):
        self.drawer.draw(offsetx=self.offset, width=self.length)

    def button_press(self, x, y, button):
        # Check if it's a right click and, if so, toggle textt
        if button == 1:
            self.set_default_timer()
            self.screen_index = (self.screen_index + 1) % len(self.screens)
            self.update()

    def set_default_timer(self):
        if self.default_timer:
            self.default_timer.cancel()

        self.default_timer = self.timeout_add(self.info_timeout,
                                              self.show_default)

    def show_default(self):
        # Show first screen
        self.screen_index = 0
        self.update()
