from dateutil.relativedelta import relativedelta
import datetime
import calendar
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class Holiday(models.Model):
    MONTHS = {
        1:  'January',
        2:  'February',
        3:  'March',
        4:  'April',
        5:  'May',
        6:  'June',
        7:  'July',
        8:  'August',
        9:  'September',
        10: 'October',
        11: 'November',
        12: 'December',
    }
    name = models.CharField(max_length=64)
    month = models.PositiveSmallIntegerField(choices=MONTHS.items())

    class Meta:
        abstract = False

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def get_date_for_year(cls, name, year=datetime.date.today().year):
        """Try to determine the date for a given holiday based on name
        and either the provided year or defaults to the current year.
        """
        # check first Custom holidays, holidays that have a custom date
        # for each year
        try:
            holiday = CustomHoliday.objects.get(name=name, year=year)
            return datetime.date(holiday.year, holiday.month, holiday.day)
        except:
            pass

        # next try Static holidays, or holidays that have the exact same
        # month/day each year
        try:
            holiday = StaticHoliday.objects.get(name=name)
            return datetime.date(year, holiday.month, holiday.day)
        except:
            pass

        # next try holidays that are a specific Nth day of a month
        # i.e. Third Monday or January == MLK Day
        try:
            holiday = NthXDayHoliday.objects.get(name=name)
            if holiday.nth < 5:
                count = 0
                date = datetime.date(year, holiday.month, 1)
                while count < holiday.nth:
                    if date.weekday() == holiday.day_of_week:
                        count += 1
                    date += relativedelta(days=1)
                date -= relativedelta(days=1)
                return date
            else:
                date = datetime.date(year, holiday.month, 
                    calendar.monthrange(year,holiday.month)[1])
                while date.weekday() != holiday.day_of_week:
                    date -= relativedelta(days=1)
                return date
        except:
            pass

        # next try holidays that are a specific Nth day of a month
        # AFTER an Nth day of a month.
        # i.e. First Tuesday after First Monday in November == USA Election Day
        try:
            holiday = NthXDayAfterHoliday.objects.get(name=name)
            count = 0
            after_count = 0
            date = datetime.date(year, holiday.month, 1)
            while count < holiday.nth or after_count < holiday.after_nth:
                if after_count >= holiday.after_day_of_week and date.weekday() == holiday.day_of_week:
                    count += 1
                if date.weekday() == holiday.after_day_of_week:
                    after_count += 1
                date += relativedelta(days=1)
            date -= relativedelta(days=1)
            return date
        except:
            pass

        # try to give a useful exception if the holiday is not found.
        # for example, if Easter is a holiday, but just not available for 2020,
        # let's tell the user that rather than saying 'Holiday not found.'
        if Holiday.objects.filter(name=name).count() > 0:
            raise ObjectDoesNotExist('Holiday with that name is found, but cannot determine date for the provided year.  Check your CustomHoliday table.')
        else:
            raise ObjectDoesNotExist('Holiday with that name cannot be found.')

    @classmethod
    def get_available_holidays(cls):
        """Returns a list of all holiday names.
        TODO: could optionally provide a year.
        """
        return [h['name'] for h in Holiday.objects.all().values('name').distinct()]

    @classmethod
    def get_holidays_for_year(cls, year=datetime.date.today().year):
        """Returns a list of holiday obects for the provided year, defaults
        to the current year.
        """
        holidays = []
        for h in StaticHoliday.objects.filter():
            holidays.append(h)
        for h in NthXDayHoliday.objects.filter():
            holidays.append(h)
        for h in NthXDayAfterHoliday.objects.filter():
            holidays.append(h)
        for h in CustomHoliday.objects.filter(year=year):
            holidays.append(h)

        # TODO: sort these
        return holidays

    @classmethod
    def is_holiday(cls, date):
        """Determines if the provided date is a holiday.  If so, returns the
        holiday object.  Otherwise returns False.
        """
        # TODO: improve how this is done, specifically the second check
        # (after checking the easy StaticHoliday table)

        # checkt the StaticHoliday to see if the month and day exist in here.
        try:
            h = StaticHoliday.objects.get(month=date.month, day=date.day)
            return h
        except:
            pass

        # check all other holidays in the year to see if the provided date
        # is a recorded holiday
        for h in cls.get_holidays_for_year(date.year):
            if cls.get_date_for_year(name=h.name, year=date.year) == date:
                return h

        # defaults to returning False
        return False

class StaticHoliday(Holiday):
    DAYS = [(i, i) for i in range(1,32)]
    
    day = models.PositiveSmallIntegerField(choices=DAYS)
    

class NthXDayHoliday(Holiday):
    NTHS = {
        1: 'First',
        2: 'Second',
        3: 'Third',
        4: 'Fourth',
        5: 'Last',
    }
    DOWS = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    nth = models.PositiveSmallIntegerField(choices=NTHS.items())
    day_of_week = models.PositiveSmallIntegerField(choices=DOWS.items())
        

class NthXDayAfterHoliday(Holiday):
    NTHS = {
        1: 'First',
        2: 'Second',
        3: 'Third',
        4: 'Fourth',
        5: 'Fifth',
    }
    DOWS = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    nth = models.PositiveSmallIntegerField(choices=NTHS.items())
    day_of_week = models.PositiveSmallIntegerField(choices=DOWS.items())
    after_nth = models.PositiveSmallIntegerField(choices=NTHS.items())
    after_day_of_week = models.PositiveSmallIntegerField(choices=DOWS.items())
        

class CustomHoliday(Holiday):
    DAYS = [(i, i) for i in range(1,32)]

    def __unicode__(self):
        return '%s %d' % (self.name, self.year)
    
    day = models.PositiveSmallIntegerField(choices=DAYS)
    year = models.PositiveSmallIntegerField()
