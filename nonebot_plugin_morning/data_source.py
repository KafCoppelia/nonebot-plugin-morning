from nonebot.adapters.onebot.v11 import MessageSegment
from typing import Union, List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from .config import *
from .utils import *
try:
    import ujson as json
except ModuleNotFoundError:
    import json

class MorningManager:
    def __init__(self):
        self._morning: Dict[str, Dict[str, Dict[str, Union[str, int, List[timedelta]]]]] = dict()
        self._morning_path: Path = morning_config.morning_path / "morning.json"
        
        self._config: Dict[str, Dict[str, Dict[str, Union[bool, int]]]] = dict()
        self._config_path: Path = morning_config.morning_path / "config.json"

    def _init_group_data(self, gid: str) -> None:
        '''
            Initialize group data
        '''
        self._load_data()
        if gid not in self._morning:
            self._morning.update({
                gid: {
                    "today_count": {
                        "good_morning": 0,
                        "good_night": 0,
                        "weekly_sleeping_king": ""
                    }
                }
            })
            
            self._save_data()

    def get_current_config(self) -> MessageSegment:
        '''
            Return current configure
        '''
        msg = "早安晚安设置如下："
        self._load_config()
        
        # morning config
        good_morning_intime = self._config["morning"]["good_morning_intime"]["enable"]
        if good_morning_intime:
            msg += "\n是否要求规定时间内起床：是\n - 最早允许起床时间：" + str(self._config["morning"]['good_morning_intime']["early_time"]) + "点\n - 最晚允许起床时间：" + str(self._config["morning"]["good_morning_intime"]["late_time"]) + "点"
        else:
            msg += "\n是否要求规定时间内起床：否"
            
        multi_get_up = self._config["morning"]["multi_get_up"]["enable"]
        if multi_get_up:
            msg += "\n是否允许连续多次起床：是"
        else:
            msg += "\n是否允许连续多次起床：否\n - 允许的最短起床间隔：" + str(self._config["morning"]["multi_get_up"]["interval"]) + "小时"
        
        super_get_up = self._config["morning"]["super_get_up"]["enable"]
        if super_get_up:
            msg += "\n是否允许超级亢奋(即睡眠时长很短)：是"
        else:
            msg += "\n是否允许超级亢奋(即睡眠时长很短)：否\n - 允许的最短睡觉时长：" + str(self._config["morning"]["super_get_up"]["interval"]) + "小时"
        
        # night config
        good_night_intime = self._config["night"]["good_night_intime"]["enable"]
        if good_night_intime:
            msg += "\n是否要求规定时间内睡觉：是\n - 最早允许睡觉时间：" + str(self._config["night"]["good_night_intime"]["early_time"]) + \
                "点\n - 最晚允许睡觉时间：第二天早上" + str(self._config["night"]["good_night_intime"]["late_time"]) + "点"
        else:
            msg += "\n是否要求规定时间内睡觉：否"
        
        good_sleep = self._config["night"]["good_sleep"]["enable"]
        if good_sleep:
            msg += "\n是否开启优质睡眠：是"
        else:
            msg += "\n是否开启优质睡眠：否\n - 允许的最短优质睡眠：" + str(self._config["night"]["good_sleep"]["interval"]) + "小时"
        
        deep_sleep = self._config["night"]["deep_sleep"]["enable"]
        if deep_sleep:
            msg += "\n是否允许深度睡眠(即清醒时长很短)：是"
        else:
            msg += "\n是否允许深度睡眠(即清醒时长很短)：否\n - 允许的最短清醒时长：" + str(self._config["night"]["deep_sleep"]["interval"]) + "小时"
        
        return MessageSegment.text(msg)

    # ------------------------------ Config ------------------------------ #
    def _change_enable(self, day_or_night: str, _setting: str, new_state: bool) -> str:
        '''
            Change and save new state of setting
        '''
        self._load_config()
        self._config[day_or_night][_setting]["enable"] = new_state
        self._save_config()

        return "配置更新成功！"

    def _change_set_time(self, _day_or_night: str, _setting: str, _interval_or_early_time: int, _late_time: Optional[int] = None) -> str:
        '''
            Change time interval
        '''
        self._load_config()
        
        if _setting == "good_morning_intime" or _setting == "good_night_intime":
            early_time = _interval_or_early_time
            if isinstance(_late_time, int):
                late_time = _late_time
            else:
                return "配置更新失败：缺少参数！"
            
            self._config[_day_or_night][_setting]["early_time"] = early_time
            self._config[_day_or_night][_setting]["late_time"] = late_time
        else:
            interval = _interval_or_early_time
            self._config[_day_or_night][_setting]["interval"] = interval
        
        msg = "配置更新成功！"
        
        if _setting == "good_morning_intime" or _setting == "good_night_intime" or _setting == "good_sleep" \
            and self._config[_day_or_night][_setting]["enable"] == False:
            self._config[_day_or_night][_setting]["enable"] = True	# True is the default setting
            msg += "且此项设置已启用！"
        
        # Some settings are False in default
        if _setting == "multi_get_up" or _setting == "super_get_up" or _setting == "deep_sleep" \
            and self._config[_day_or_night][_setting]["enable"] == True:
            self._config[_day_or_night][_setting]["enable"] = False	# False is the default setting
            msg += "且此项设置已禁用！"
        
        self._save_config()
        
        return msg
    
    def reset_data(self) -> None:
        '''
            刷新群一天早晚安数据，群早安晚安计数置0
        '''
        self._load_data()
        for gid in self._morning:
            self._morning[gid]["today_count"]["morning"] = 0
            self._morning[gid]["today_count"]["night"] = 0
        
        self._save_data()

    def morning_config(self, _mor_setting: str, *args: List[int]) -> MessageSegment:
        '''
            Config about morning
        '''
        _setting = mor_switcher[_mor_setting]
        if _setting == "good_morning_intime":
            early_time = args[0]
            late_time = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("morning", _setting, early_time, late_time)
        else:
            interval = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("morning", _setting, interval)
        
        return MessageSegment.text(msg)

    def morning_switch(self, _mor_setting: str, new_state: bool) -> MessageSegment:
        '''
            Enable/Disable of morning settings
        '''
        _setting = mor_switcher[_mor_setting]
        msg = self._change_enable("morning", _setting, new_state)
        
        return MessageSegment.text(msg)

    def night_config(self, _nig_setting: str, *args: List[int]) -> MessageSegment:
        '''
            Config about night
        '''
        _setting = nig_switcher[_nig_setting]
        if _setting == "good_night_intime":
            early_time = args[0]
            late_time = args[1]
            
            if early_time < 0 or early_time > 24 or late_time < 0 or late_time > 24:
                msg = "错误！您设置的时间未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("night", _setting, early_time, late_time)
        else:
            interval = args[0]
            
            if interval < 0 or interval > 24:
                msg = "错误！您设置的时间间隔未在0-24之间，要求：0 <= 时间 <= 24"
            else:
                msg = self._change_set_time("night", _setting, interval, None)
        
        return MessageSegment.text(msg)

    def night_switch(self, _nig_setting: str, new_state: bool) -> MessageSegment:
        '''
            Enable/Disable of night settings
        '''
        _setting = nig_switcher[_nig_setting]
        msg = self._change_enable("night", _setting, new_state)
        
        return MessageSegment.text(msg)

    # ------------------------------ Morning Judgement ------------------------------ #
    def _morning_and_update(self, gid: str, uid: str, now_time: datetime) -> Tuple[str, Union[str, int]]:
        '''
            Morning & update data
        '''
        # 起床并写数据
        sleep_time: datetime = datetime.strptime(self._morning[gid][uid]["sleep_time"], "%Y-%m-%d %H:%M:%S")
        in_sleep = now_time - sleep_time
        secs = in_sleep.total_seconds()
        day = secs // (3600 * 24)
        hour: int = int((secs - day * 3600 * 24) // 3600)
        minute: int = int((secs - day * 3600 * 24 - hour * 3600) // 60)
        second: int = int(secs - day * 3600 * 24 - hour * 3600 - minute * 60)
        
        # 睡觉时间小于24小时就同时给出睡眠时长，否则隔日
        in_sleep_tmp: Union[str, int] = 0
        if day == 0:
            in_sleep_tmp = str(hour) + "时" + str(minute) + "分" + str(second) + "秒"
        else:
            in_sleep_tmp = 0
        
        self._load_data()
        self._morning[gid][uid]["get_up_time"] = now_time.strftime("%Y-%m-%d %H:%M:%S")
        self._morning[gid][uid]["morning_count"] += 1
        
        # 判断是今天第几个起床的
        self._morning[gid]["today_count"]["morning"] += 1
        self._save_data()

        return self._morning[gid]["today_count"]["morning"], in_sleep_tmp

    def get_morning_msg(self, gid: str, uid: str, sex_str: str) -> MessageSegment:
        '''
            Return good morning info
        '''
        self._load_config()
        msg: str = ""
        
        # 若开启规定时间早安，则判断该时间是否允许早安
        now_time: datetime = datetime.now()
        if self._config["morning"]["good_morning_intime"]["enable"]:
            _early_time: int = self._config["morning"]["good_morning_intime"]["early_time"]
            _late_time: int = self._config["morning"]["good_morning_intime"]["late_time"]
            if not is_MorTimeinRange(_early_time, _late_time, now_time):
                msg = f"现在不能早安哦，可以早安的时间为{_early_time}时到{_late_time}时~"
                return MessageSegment.text(msg)

        self._init_group_data(gid)
        
        # 当数据里有过这个人的信息就判断：是否隔日
        last_sleep_time: str = self._morning[gid][uid]["good_night_time"]
        if uid in self._morning[gid] and is_TimeinInterval(last_sleep_time, now_time, 24):
            
            # 若关闭连续多次早安，则判断在设定时间内是否多次早安
            if not self._config["morning"]["multi_get_up"]["enable"] and self._morning[gid][uid]["get_up_time"] != 0:
                interval: int = self._config["morning"]["multi_get_up"]["interval"]
                good_morning_time: str = self._morning[gid][uid]["good_morning_time"]
                if is_TimeinInterval(good_morning_time, now_time, interval):
                    msg = f"{interval}小时内你已经早安过了哦~"
                    return MessageSegment.text(msg)
            
            # 若关闭超级亢奋，则判断睡眠时长是否小于设定时间
            if not self._config["morning"]["super_get_up"]["enable"]:
                interval: int = self._config["morning"]["super_get_up"]["interval"]
                good_night_time: str = self._morning[gid][uid]["good_night_time"]
                if is_TimeinInterval(good_night_time, now_time, interval):
                    msg = "你可猝死算了吧？现在不能早安哦~"
                    return MessageSegment.text(msg)
                  
        # 否则说明：他还没睡过觉、或为隔日早安
        else:
            msg = "你还没睡过觉呢！不能早安哦~"
            return MessageSegment.text(msg)
            
        # 当前面条件均符合的时候，允许早安
        num, in_sleep = self._morning_and_update(gid, uid, now_time)
        if isinstance(in_sleep, str):
            msg = f"早安成功！你的睡眠时长为{in_sleep}，\n你是今天第{num}个起床的{sex_str}！"
        else:
            msg = "你还没睡过觉呢！不能早安哦~"
 
        return MessageSegment.text(msg)

    # ------------------------------ Night Judgement ------------------------------ #
    def _night_and_update(self, gid: str, uid: str, now_time: datetime) -> Tuple[str, Union[str, int]]:
        '''
            Good night & update
        '''
        self._load_data()
        
        # 没有晚安数据，则创建
        if uid not in self._morning[gid]:
            self._morning[gid].update({
                uid: {
                    "good_morning_time": 0,			# 早安时间
                    "good_night_time": 				# 晚安时间
                        now_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "good_morning_count": 0,		# 总晚安天数
                    "good_night_count": 1,			# 总早安天数
                    "weekly_good_morning_count": 0,	# 周早安天数
                    "weekly_good_night_count": 0,	# 周晚安天数
                    "weekly_sleep_time": [],		# 周每天睡眠时长，type: List[timedelta]
                    "latest_good_night_time": 0,	# 周晚安最晚的时间
                    "earliest_good_morning_time": 0	# 周早起最早的时间
                }
            })
            
            self._morning[gid][uid]["latest_good_night_time"] = self._morning[gid][uid]["good_night_time"]
            
        # 若有就更新数据
        else:
            # Record today's sleep time
            self._morning[gid][uid]["good_night_time"] = now_time.strftime("%Y-%m-%d %H:%M:%S")
            # Total night count add
            self._morning[gid][uid]["good_night_count"] += 1
            # Weekly night count add
            self._morning[gid][uid]["weekly_good_night_count"] += 1
            
            # If today's sleep time later, update latest_sleep_time
            if is_later(self._morning[gid][uid]["good_night_time"], self._morning[gid][uid]["latest_good_night_time"]):
                self._morning[gid][uid]["latest_good_night_time"] = self._morning[gid][uid]["good_night_time"]
          
        # 当上次起床时间不是初始值0,就计算清醒的时长
        in_day_tmp: Union[str, int] = 0
        if self._morning[gid][uid].get("good_morning_time", 0) != 0:
            get_up_time = datetime.strptime(self._morning[gid][uid]["good_morning_time"], "%Y-%m-%d %H:%M:%S")
            in_day = now_time - get_up_time
            secs = in_day.total_seconds()
            day = secs // (3600 * 24)
            hour: int = int((secs - day * 3600 * 24) // 3600)
            minute: int = int((secs - day * 3600 * 24 - hour * 3600) // 60)
            second: int = int(secs - day * 3600 * 24 - hour * 3600 - minute * 60)
            
            if day == 0:
                in_day_tmp = str(hour) + "时" + str(minute) + "分" + str(second) + "秒"
            else:
                in_day_tmp = 0
                
        # 判断是今天第几个睡觉的
        self._morning[gid]["today_count"]["good_night"] += 1
        self._save_data()

        return self._morning[gid]["today_count"]["good_night"], in_day_tmp

    def get_night_msg(self, gid: str, uid: str, sex_str: str) -> MessageSegment:
        '''
            Return good night info
        '''
        self._load_config()
        msg: str = ""
        
        # 若开启规定时间晚安，则判断该时间是否允许晚安
        now_time: datetime = datetime.now()
        if self._config["night"]["good_night_intime"]["enable"]:
            _early_time: int = self._config["night"]["good_night_intime"]["early_time"]
            _late_time: int = self._config["night"]["good_night_intime"]["late_time"]
            if not is_NigTimeinRange(_early_time, _late_time, now_time):
                msg = f'现在不能晚安哦，可以晚安的时间为{_early_time}时到第二天早上{_late_time}时~'
                return MessageSegment.text(msg)

        self._init_group_data(gid)

        # 当数据里有过这个人的信息就判断:
        if uid in self._morning[gid]:
            
            # 若开启优质睡眠，则判断在设定时间内是否多次晚安
            if self._config["night"]["good_sleep"]["enable"]:
                interval: int = self._config["night"]["good_sleep"]["interval"]
                good_night_time: str = self._morning[gid][uid]["good_night_time"]
                if is_TimeinInterval(good_night_time, now_time, interval):
                    msg = f'{interval}小时内你已经晚安过了哦~'
                    return MessageSegment.text(msg)
            
            # 若关闭深度睡眠，则判断不在睡觉的时长是否小于设定时长
            good_morning_time: Union[str, int] = self._morning[gid][uid].get("good_morning_time", 0)
            if not self._config["night"]["deep_sleep"]["enable"] and isinstance(good_morning_time, str):
                interval: int = self._config["night"]["deep_sleep"]["interval"]
                if is_TimeinInterval(good_morning_time, now_time, interval):
                    msg = "睡这么久还不够？现在不能晚安哦~"
                    return MessageSegment.text(msg)

        # 当数据里没有这个人或者前面条件均符合的时候，允许晚安
        num, in_day = self._night_and_update(gid, uid, now_time)
        if isinstance(in_day, int):
            msg = f'晚安成功！你是今天第{num}个睡觉的{sex_str}！'
        else:
            msg = f'晚安成功！你今天的清醒时长为{in_day}，\n你是今天第{num}个睡觉的{sex_str}！'
            
        return MessageSegment.text(msg)
    
    # ------------------------------ Routine ------------------------------ #
    def get_my_routine(self, gid: str, uid: str) -> MessageSegment:
        self._init_group_data(gid)
        
        if uid in self._morning[gid]:
            get_up_time: str = self._morning[gid][uid]["good_morning_time"]
            sleep_time: str = self._morning[gid][uid]["good_night_time"]
            morning_count: int = self._morning[gid][uid]["morning_count"]
            night_count: int = self._morning[gid][uid]["night_count"]
            
            msg = "你的作息数据如下："
            msg += f"\n最近一次早安时间为{get_up_time}"
            msg += f"\n最近一次晚安时间为{sleep_time}"
            msg += f"\n一共早安了{morning_count}次"
            msg += f"\n一共晚安了{night_count}次"
        else:
            msg = "你还没有早安晚安过呢！暂无数据~"
        
        return MessageSegment.text(msg)

    def get_group_routine(self, gid: str) -> MessageSegment:
        self._init_group_data(gid)
        
        moring_count: int = self._morning[gid]["today_count"]["good_morning"]
        night_count: int = self._morning[gid]["today_count"]["good_night"]
        
        msg = f"今天已经有{moring_count}位群友早安了，{night_count}位群友晚安了~"

        return MessageSegment.text(msg)

    # ------------------------------ Utils ------------------------------ #
    def _save_data(self) -> None:
        with open(self._morning_path, 'w', encoding='utf-8') as f:
            json.dump(self._morning, f, ensure_ascii=False, indent=4)
                
    def _save_config(self) -> None:
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=4)

    def _load_data(self) -> None:
        with open(self._morning_path, "r", encoding="utf-8") as f:
            self._morning = json.load(f)
        
    def _load_config(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)

morning_manager = MorningManager()

__all__ = [
    morning_manager
]