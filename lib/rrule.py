from dateutil import parser

class RRule:
    def __init__(self, start, rule_string):
        self._freq_map = {
            "yearly": "year",
            "monthly": "month",
            "weekly": "week",
            "daily": "day",
            "hourly": "hour",
            "minutely": "minute",
            "secondly": "second"
        }
        self._month_list = ['months_start_at_1', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        self._weekday_map = {
            "mo": "mon",
            "tu": "tue",
            "we": "wed",
            "th": "thu",
            "fr": "fri",
            "sa": "sat",
            "su": "sun"
        }
        self.dtstart = start
        self._parse(rule_string)

    def _handle_freq(self, rrkwargs, name, value):
        rrkwargs[name] = self._freq_map[value]

    def _handle_count(self, rrkwargs, name, value):
        rrkwargs[name] = value

    def _handle_until(self, rrkwargs, name, value):
        try:
            rrkwargs[name] = parser.parse(value)
        except ValueError:
            raise ValueError("invalid until date")

    def _handle_interval(self, rrkwargs, name, value):
        rrkwargs[name] = f"{value}"

    def _handle_bymonth(self, rrkwargs, name, value):
        # TODO rrkwargs[name] = [self._month_list[int(x)] for x in value.split(',')]
        pass

    def _handle_wkst(self, rrkwargs, name, value):
        # TODO rrkwargs[name] = self._weekday_map[value]
        pass

    def _handle_byday(self, rrkwargs, name, value):
        rrkwargs[name] = [self._weekday_map[x] for x in value.split(',')]

    def __str__(self):
        s = "every"

        if 'interval' in self.rrkwargs:
            s += f" {self.rrkwargs['interval']} {self.rrkwargs['freq']}s"
        elif 'byday' in self.rrkwargs:
            s += f" {','.join(self.rrkwargs['byday'])}"
        else:
            s += f" {self.rrkwargs['freq']}"

        if 'count' in self.rrkwargs:
            s += f" for {self.rrkwargs['count']} {self.rrkwargs['freq']}s"

        s += f" starting {self.dtstart.date().isoformat()}"

        if 'until' in self.rrkwargs:
            s += f" ending {self.rrkwargs['until'].date().isoformat()}"

        return s

    def _parse(self, rule_string):
        line = rule_string.split(':')[1]
        self.rrkwargs = {}
        for pair in line.split(';'):
            name, value = pair.split('=')
            name = name.lower()
            value = value.lower()
            try:
                getattr(self, "_handle_"+name)(self.rrkwargs, name, value)
            except AttributeError:
                raise ValueError("unknown parameter '%s'" % name)
            except (KeyError, ValueError):
                raise ValueError("invalid '%s': %s" % (name, value))

# ~@:-]
