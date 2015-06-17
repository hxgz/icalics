#!/usr/bin/python  
#-*-coding:utf-8-*-

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from urllib2 import urlopen
import json,datetime
from ics import Calendar, Event

import Config
class Holiday(Calendar):
    """
    generate Chinese Holiday
    """
    _FREEDAY="休息日"
    _WORKDAY="工作日"
    def __init__(self, imports=None, events=None, creator="介川",title="假日"):
        super(Holiday,self).__init__(imports,events,creator,title=title)
    def _fixup(self,year,DateInfos):
        """
        修正假日返回的结果
        日期为周六-日，是休息日，则去掉休息日不显示。不然则是工作日
        """
        from dateutil import rrule

        weekend = set([5, 6])

        for dt in rrule.rrule(rrule.DAILY,
                              dtstart=datetime.datetime.strptime(year, '%Y'),
                              until=datetime.datetime.strptime(str(int(year)+1), '%Y') + datetime.timedelta(days=-1)):
            _yearmonthday=dt.strftime('%Y%m%d')
            if dt.weekday() in weekend:
                try:
                    if DateInfos[_yearmonthday] == self._FREEDAY:
                        day_before = dt+datetime.timedelta(days=-1)
                        day_after = dt+datetime.timedelta(days=1)

                        if (dt.weekday() == 5 and DateInfos.get(day_before.strftime('%Y%m%d')) != self._FREEDAY) or (dt.weekday() == 6 and DateInfos.get(day_after.strftime('%Y%m%d')) != self._FREEDAY):
                            del DateInfos[_yearmonthday]
                except KeyError:
                    DateInfos[_yearmonthday] = self._WORKDAY

        return DateInfos
    def _get_holiday(self,year):
        months=[year+ "%02d" % x for x in range(1,13)]
        holiday_url = 'http://www.easybots.cn/api/holiday.php?m=%s' % ",".join(months)

        DateInfos={}
        try:
            response = urlopen(holiday_url,timeout=5)
        #except socket.timeout as e:
        except Exception as e:
            print e
            return {}
        #输出json格式：工作日对应结果为 0,休息日对应结果为 1, 节假日对应的结果为 2；
        resp_json = json.loads(response.read())
        for month in resp_json:
            for day in resp_json[month]:
                if "0" == resp_json[month][day]:
                    print resp_json[month][day]
                    DateInfos[month+day] = self._WORKDAY
                elif "1" == resp_json[month][day] or "2" == resp_json[month][day]:
                    DateInfos[month+day] = self._FREEDAY
        return DateInfos

    def append(self,year):
        for _date,_info in self._fixup(year,self._get_holiday(year)).iteritems():
            e = Event()
            e.name = _info
            e.begin = '%s-%s-%s' % (year,_date[4:6],_date[6:8])
            e.make_all_day()
            e.description="Edited by 介川"
            self.events.append(e)

    def dump(self,file):
        with open(file, 'w') as f:
            f.writelines(self)
        
class LumarTaboo(Calendar):
    """
    The almanac and taboo class
    """
    def __init__(self, imports=None, events=None, creator="介川",title="五行命理"):
        super(LumarTaboo,self).__init__(imports,events,creator,title=title)
    def __get_lumar_taboo(self,year):
        unescape_crlf='\\n'
        #宜凶
        yj_url = 'http://51wnl.com/YJData/%s.json' % year 
        #命理
        lumar_url = 'http://51wnl.com/moreLumarData/%s.json' % year

        DateInfos={}
        try:
            response = urlopen(yj_url,timeout=5)
        except Exception as e:
            print "Fail to get YJData,E:",e
            return DateInfos
        resp_json = json.loads(response.read())
        def _get_keyname(key):
            if key == "y":
                return "宜"
            elif key == "j":
                return "忌"
            elif key == "pzbj":
                return "彭祖百忌"
            elif key == "jsyq":
                return "吉神宜趋"
            elif key == "xsyj":
                return "凶神宜忌"
            elif key == "cs":
                return "冲煞"
            elif key == "wx":
                return "五行"
            else:
                return ""
        for _mmdd,_info in resp_json.iteritems():
            DateInfos[year+_mmdd[1:]] = unescape_crlf.join([_get_keyname(k)+":"+v for k,v in _info.iteritems()])

        try:
            response = urlopen(lumar_url,timeout=5)
        except Exception as e:
            print "Fail to get LumarData,E:",e
            return DateInfos
        resp_json = json.loads(response.read())
        for _mmdd,_info in resp_json.iteritems():
            if year+_mmdd in DateInfos:
                ldinfos = [_get_keyname(k)+":"+v for k,v in _info.iteritems()]
                ldinfos.append(DateInfos[year+_mmdd])

                DateInfos[year+_mmdd] = unescape_crlf.join(ldinfos)
            else:
                DateInfos[year+_mmdd] = unescape_crlf.join([_get_keyname(k)+":"+v for k,v in _info.iteritems()])

        return DateInfos

    def append(self,year):
        for _date,_info in self.__get_lumar_taboo(year).iteritems():
            e = Event()
            e.name = "五行命理"
            e.begin = '%s-%s-%s 00:00:00' % (year,_date[4:6],_date[6:8])
            e.make_all_day()
            e.description=_info
            self.events.append(e)

    def dump(self,file):
        with open(file, 'w') as f:
            f.writelines(self)

def dump_holiday(year):
    h=Holiday()
    for index in range(Config.ics_duration[0],Config.ics_duration[1]+1):
        h.append(str(int(year)+index))
    h.dump(Config.holiday_file)
def dump_lumartaboo(year):
    lt=LumarTaboo()
    for index in range(Config.ics_duration[0],Config.ics_duration[1]+1):
        lt.append(str(int(year)+index))
    lt.dump(Config.lumar_file)

def main():
    now=datetime.datetime.now()
    dump_holiday(now.year)
    if Config.luma_type:
        dump_lumartaboo(now.year)
if __name__ == "__main__":
    main()

