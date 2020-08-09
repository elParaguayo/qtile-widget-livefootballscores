# Live Football Scores Widget

This module provides a simple widget showing the live football (soccer for any of you in the US) scores.

## About

The module uses a module I wrote a number of years ago that parses data from the BBC Sport website.

The underlying module needs work so it will probably only work if you pick a "big" team.

## Demo

Here is a screenshot from my HTPC showing the widget in the bar.

![Screenshot](images/livefootballscores.gif?raw=true)</br>
(The different screens show: live score, elapsed time, home and away goalscorers and competition name. In addition, the amount of text shown can be customised by using python's string formatting techniques e.g. the default line "{H:.3} {h}-{a} {A:.3}" shows the first 3 letters of team names rather than the full name as shown above.)


## Installation

You can clone the repository and run:

```
python setup.py install
```
or, for Arch users, just copy the PKGBUILD file to your machine and build.

## Configuration

Add the code to your config (`~/.config/qtile/config.py`):

```python
from livefootballscores import LiveFootballScoresWidget
...
screens = [
    Screen(
        top=bar.Bar(
            [
                widget.CurrentLayout(),
                widget.GroupBox(),
                widget.Prompt(),
                widget.WindowName(),
                LiveFootballScoresWidget(team="St Mirren"),     # As shown in screenshot
                widget.Clock(format='%Y-%m-%d %a %I:%M %p'),
                widget.QuickExit(),
            ],
            24,
        ),
    ),
]
```

## Customising

The widget allows the battery icon to be resized and to display colours for different states.

The widget can be customised with the following arguments:

<table>
        <tr>
                <td>font</td>
                <td>Default font</td>
        </tr>
        <tr>
                <td>fontsize</td>
                <td>Font size</td>
        </tr>
        <tr>
                <td>font_colour</td>
                <td>Text colour</td>
        </tr>
        <tr>
                <td>team</td>
                <td>Team whose scores you want to display</td>
        </tr>
        <tr>
                <td>status_text</td>
                <td>Default widget match text</td>
        </tr>
        <tr>
                <td>info_text</td>
                <td>Add extra text lines which can be displayed by clicking on widget.
        Available fields are:</br>
         {H}: Home Team name</br>
         {A}: Away Team name</br>
         {h}: Home score</br>
         {a}: Away score</br>
         {C}: Competition</br>
         {v}: Venue</br>
         {T}: Display time (kick-off, elapsed time, HT, FT)</br>
         {S}: Status (as above but no elapsed time)</br>
         {G}: Home goalscorers</br>
         {g}: Away goalscorers</br>
         {R}: Home red cards</br>
         {r}: Away red cards</td></blockquote>
        </tr>
        <tr>
                <td>refresh_interval</td>
                <td>Time to update data</td>
        </tr>
        <tr>
                <td>info_timeout</td>
                <td>Time before reverting to default text</td>
        </tr>
</table>


## Contributing

If you've used this (great, and thank you) you will find bugs so please [file an issue](https://github.com/elParaguayo/qtile-widget-laptopbattery/issues/new).
