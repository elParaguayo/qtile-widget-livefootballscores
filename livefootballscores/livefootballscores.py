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
            ["{T:^12}",
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
        ("info_timeout", 5, "Time before reverting to default text"),
        ("goal_indicator", "009999", "Colour of line to show team that scores"),
        ("red_card_indicator", "bb0000", "Colour of line to show team has had a player sent off."),
        ("always_show_red", True, "Continue to show red card indicator"),
        ("underline_status", True, "Bar at bottom of widget to indicate status."),
        ("status_fixture", "000000", "Colour when match has not started"),
        ("status_live", "008800", "Colour when match has not started"),
        ("status_halftime", "aaaa00", "Colour when match has not started"),
        ("status_fulltime", "666666", "Colour when match has not started"),
    ]

    def __init__(self, **config):
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(LiveFootballScoresWidget.defaults)
        self.add_defaults(base.MarginMixin.defaults)

        self.reset_flags()

        # Create foorball match object
        self.match = FootballMatch(self.team,
                                   detailed=True,
                                   on_goal=self.match_event,
                                   on_red=self.match_event,
                                   on_status_change=self.match_event,
                                   on_new_match=self.match_event)



        # Define our screens
        self.screens = [self.status_text] + self.info_text
        self.screen_index = 0

        # Initial variables to hide text
        self.show_text = False
        self.default_timer = None
        self.refresh_timer = None
        self.queue_timer = None

    def reset_flags(self):
        self.homegoal = False
        self.awaygoal = False
        self.statuschange = False
        self.homered = False
        self.awayred = False

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)
        self.set_refresh_timer()
        self.queue_update()

    def set_refresh_timer(self):
        self.refresh_timer = self.timeout_add(self.refresh_interval,
                                              self.refresh)

    def refresh(self):
        self.reset_flags()
        self.match.update()
        self.set_refresh_timer()
        self.queue_update()

    def match_event(self, event):
        if event.isGoal:
            self.homegoal = event.home
            self.awaygoal = not event.home

        elif event.isRed:
            self.homered = event.home
            self.awayred = not event.home

        elif event.isStatusChange:
            self.statuschange = True

        if any([self.homegoal, self.awaygoal, self.homered, self.awayred,
                self.statuschange]):
            self.queue_update()

    def queue_update(self):
        if self.queue_timer:
            self.queue_timer.cancel()

        self.queue_timer = self.timeout_add(1, self.update)

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

        if self.screen_index == 0:
            if self.homegoal:
                self.draw_goal(True)

            if self.awaygoal:
                self.draw_goal(False)

            if self.homered or (self.always_show_red and
                                self.match.HomeRedCards):
                self.draw_red(True)

            if self.awayred or (self.always_show_red and
                                self.match.AwayRedCards):
                self.draw_red(False)

            if self.underline_status:
                self.draw_underline()

        # Redraw the bar
        self.bar.draw()

    def draw_goal(self, home):
        offset = 0 if home else (self.width - 2)

        self.drawer.set_source_rgb(self.goal_indicator)

        # Draw the bar
        self.drawer.fillrect(offset,
                             0,
                             2,
                             self.height,
                             2)

    def draw_red(self, home):
        offset = 0 if home else (self.width - 2)

        self.drawer.set_source_rgb(self.red_card_indicator)

        # Draw the bar
        self.drawer.fillrect(offset,
                             self.height/2,
                             2,
                             self.height/2,
                             2)

    def draw_underline(self):
        offset = 2
        width = self.width - 2

        m = self.match

        if m.isFixture:
            fill = self.status_fixture
        elif m.isLive:
            fill = self.status_live
        elif m.isHalfTime:
            fill = self.status_halftime
        elif m.isFinished:
            fill = self.status_fulltime
        else:
            fill = "000000"

        self.drawer.set_source_rgb(fill)

        # Draw the bar
        self.drawer.fillrect(offset,
                             self.height - 2,
                             width,
                             2,
                             2)

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
