from libqtile.widget import base
from libqtile import bar, images
from libqtile.log_utils import logger

from .footballscores import FootballMatch, League, FSConnectionError


# Massively overkill to use a class here...
class MatchFlags(object):

    def __init__(self):
        self._reset()

    def _reset(self):
        self.homegoal = False
        self.awaygoal = False
        self.statuschange = False
        self.homered = False
        self.awayred = False

    @property
    def changes(self):
        return any([self.homegoal,
                    self.awaygoal,
                    self.statuschange,
                    self.homered,
                    self.awayred])

    def reset(self):
        self._reset()


class LiveFootballScoresWidget(base._Widget, base.MarginMixin):

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size"),
        ("font_colour", "ffffff", "Text colour"),
        ("team", "Liverpool", "Team whose scores you want to display"),
        ("teams", [], "List of other teams you want to display"),
        ("leagues", [], "List of leagues you want to display"),
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
        ("startup_delay", 30, "Time before sending first web request"),
        ("goal_indicator", "009999", "Colour of line to show team that scores"),
        ("red_card_indicator", "bb0000", "Colour of line to show team has had a player sent off."),
        ("always_show_red", True, "Continue to show red card indicator"),
        ("underline_status", True, "Bar at bottom of widget to indicate status."),
        ("status_fixture", "000000", "Colour when match has not started"),
        ("status_live", "008800", "Colour when match is live"),
        ("status_halftime", "aaaa00", "Colour when half time"),
        ("status_fulltime", "666666", "Colour when match has ended"),
    ]

    def __init__(self, **config):
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(LiveFootballScoresWidget.defaults)
        self.add_defaults(base.MarginMixin.defaults)
        self.flags = {}
        self.reset_flags()

        self.sources = ([],[],[])
        self.matches = []
        self.match_index = 0

        # Define our screens
        self.screens = [self.status_text] + self.info_text
        self.screen_index = 0

        # Initial variables to hide text
        self.show_text = False
        self.default_timer = None
        self.refresh_timer = None
        self.queue_timer = None

    def reset_flags(self):
        for flag in self.flags:
            self.flags[flag].reset()

    def reboot(self):
        """
        Sometimes the widget won't update (and I don't know why).
        This method should reset everything and start the widget again.

        Can be bound to a key e.g.:
           lazy.widget["livefootballscoreswidget"].reboot
        """

        timers = [self.queue_timer, self.default_timer, self.refresh_timer]
        _ = [timer.cancel() for timer in timers if timer]

        self.flags = {}
        self.matches = []
        self.sources = ([],[],[])

        self.timeout_add(1, self.setup)

        return True

    def cmd_reboot(self):
        return self.reboot()

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)
        self.matches = []
        self.timeout_add(self.startup_delay, self.setup)

    def setup(self):
        kwargs = {"detailed": True,
                  "on_goal": self.match_event,
                  "on_red": self.match_event,
                  "on_status_change": self.match_event,
                  "on_new_match": self.match_event}

        try:
            # Create foorball match object
            if not self.sources[0]:
                myteam = FootballMatch(self.team, **kwargs)
                self.sources[0].append(myteam)

            if not self.sources[1] and self.teams:
                self.sources[1].clear()
                for team in self.teams:
                    self.sources[1].append(FootballMatch(team, **kwargs))

            if not self.sources[2] and self.leagues:
                self.sources[2].clear()
                for league in self.leagues:
                    self.sources[2].append(League(league, **kwargs))

            self.get_matches()
            self.set_refresh_timer()
            self.queue_update()

        except FSConnectionError:

            logger.warning("Unable to get football scores data.")

            # Check if we managed to create all teams and leagues objects
            if len(self.sources[1]) != len(self.teams):
                self.sources[1].clear()

            if len(self.sources[2]) != len(self.leagues):
                self.sources[2].clear()

            # Can't connect, so let's try again later
            self.timeout_add(5, self.setup)

    def get_matches(self):
        self.matches = []

        if self.sources[0]:
            self.matches.extend([x for x in self.sources[0] if x])

        if self.sources[1]:
            self.matches.extend([x for x in self.sources[1] if x])

        if self.sources[2]:
            for league in self.sources[2]:
                if league:
                    # League object has iterator methods so can be treated as a list
                    self.matches.extend(league)

        self.set_flags()

    def set_flags(self):
        for m in self.matches:
            if m.HomeTeam not in self.flags:
                self.flags[m.HomeTeam] = MatchFlags()

        current = [x.HomeTeam for x in self.matches]

        for old in [x for x in self.flags if x not in current]:
            del self.flags[old]

    def set_refresh_timer(self):
        self.refresh_timer = self.timeout_add(self.refresh_interval,
                                              self.refresh)

    def refresh(self):
        success = False
        self.reset_flags()
        try:
            if self.sources[0]:
                _ = [x.update() for x in self.sources[0]]

            if self.sources[1]:
                _ = [x.update() for x in self.sources[1]]

            if self.sources[2]:
                _ = [x.update() for x in self.sources[2]]

            self.get_matches()

            self.queue_update()

            success = True

        except FSConnectionError:
            logger.warning("Unable to refresh football scores data.")
            if self.queue_timer:
                self.queue_timer.cancel()

        self.set_refresh_timer()

        return success

    def match_event(self, event):

        self.set_flags()

        team = event.match.HomeTeam

        try:
            flags = self.flags[team]
        except KeyError:
            # This should only happen when a new match for watched teams appears
            # Events are fired on first time, before they can be added to the flags
            # It should be safe to ignore this as the flags will be updated separately
            self.flags[team] = MatchFlags()
            flags = self.flags[team]

        if event.isGoal:
            flags.homegoal = event.home
            flags.awaygoal = not event.home

        elif event.isRed:
            flags.homered = event.home
            flags.awayred = not event.home

        elif event.isStatusChange:
            flags.statuschange = True

        if flags.changes:
            self.queue_update()

    def queue_update(self):
        if self.queue_timer:
            self.queue_timer.cancel()

        self.queue_timer = self.timeout_add(1, self.bar.draw)

    def get_match(self):

        if self.match_index >= len(self.matches):
            self.match_index = 0

        try:
            return self.matches[self.match_index]
        except IndexError:
            return None

    def calculate_length(self):

        m = self.get_match()

        if m:
            screen = self.screens[self.screen_index]
            text = m.formatText(screen)
        else:
            text = ""

        width, _ = self.drawer.max_layout_size(
            [text],
            self.font,
            self.fontsize
        )

        return width + 2 * self.margin

    def draw(self):
        # Remove background
        self.drawer.clear(self.background or self.bar.background)

        m = self.get_match()

        if m:
            screen = self.screens[self.screen_index]
            text = m.formatText(screen)
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

        if m:

            flags = self.flags[m.HomeTeam]

            if self.screen_index == 0:
                if flags.homegoal:
                    self.draw_goal(True)

                if flags.awaygoal:
                    self.draw_goal(False)

                if flags.homered or (self.always_show_red and
                                     m.HomeRedCards):
                    self.draw_red(True)

                if flags.awayred or (self.always_show_red and
                                     m.AwayRedCards):
                    self.draw_red(False)

                if self.underline_status:
                    self.draw_underline(m)

        # # Redraw the bar
        # self.bar.draw()
        self.drawer.draw(offsetx=self.offset, width=self.length)

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

    def draw_underline(self, m):
        offset = 2
        width = self.width - 2

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

    # def draw(self):
    #     self.drawer.draw(offsetx=self.offset, width=self.length)

    def button_press(self, x, y, button):
        # Check if it's a right click and, if so, toggle textt
        if button == 1:
            self.set_default_timer()
            self.screen_index = (self.screen_index + 1) % len(self.screens)
            self.bar.draw()

        elif button == 4:
            self.change_match(1)

        elif button == 5:
            self.change_match(-1)

    def change_match(self, step):
        self.screen_index = 0
        if self.matches:
            self.match_index = (self.match_index + step) % len(self.matches)
            self.bar.draw()


    def set_default_timer(self):
        if self.default_timer:
            self.default_timer.cancel()

        self.default_timer = self.timeout_add(self.info_timeout,
                                              self.show_default)

    def show_default(self):
        # Show first screen
        self.screen_index = 0
        self.bar.draw()

    def cmd_info(self):
        str_team = self.team
        str_teams = ",".join(self.teams)
        str_leagues = ",".join(self.leagues)
        obj_team = ",".join([str(team) for team in self.sources[0]])

        obj_teams = {}
        for team in self.sources[1]:
            obj_teams[team.myteam] = str(team)

        obj_leagues = {}
        for league in self.sources[2]:
            obj_leagues[league.league] = {}
            for i, m in enumerate(league):
                obj_leagues[league.league][i] = str(m)

        matches = {}
        for i, m in enumerate(self.matches):
            matches[i] = str(m)

        return {"name": self.name,
                "sources": {
                    "team": str_team,
                    "teams": str_teams,
                    "leagues": str_leagues
                },
                "objects": {
                    "team": obj_team,
                    "teams": obj_teams,
                    "leagues": obj_leagues
                },
                "matches": matches
                }

    def cmd_refresh(self):
        return self.refresh()
