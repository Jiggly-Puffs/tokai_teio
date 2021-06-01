# -*- coding: utf-8 -*-

import enum


class RESPCODE(enum.Enum):
	RESULT_CODE_OK = 1
	DB_ERROR = 100
	MAINTENANCE = 101
	SERVER_ERROR = 102
	DB_CONNECT_ERROR = 103
	SITE_DISABLE = 104
	MEMCACHE_CONNECT_ERROR = 105
	REDIS_CONNECT_ERROR = 106
	ACCESS_ERROR = 200
	SESSION_ERROR = 201
	AUTH_ERROR = 202
	ACCOUNT_BLOCK_ERROR = 203
	VERSION_ERROR = 204
	PARAM_ERROR = 205
	POST_DATA_ERROR = 206
	NG_WORD_ERROR = 207
	DOUBLE_CLICK_ERROR = 208
	HASH_ERROR = 209
	DEVICE_ERROR = 210
	DEVICE_NAME_ERROR = 211
	BOT_ACCESS_ATTACK_ERROR = 212
	CLIENT_OWN_NUM_ERROR = 213
	RESOURCE_VERSION_ERROR = 214
	NOTIFY_PREPARATION_SERVICE = 215
	PAYMENT_HISTORY_ERROR = 300
	PAYMENT_ALREADY_ERROR = 301
	PRODUCT_DATA_CSV_ERROR = 302
	PAYMENT_RECEIPT_ERROR = 303
	PAYMENT_LIMIT_ERROR = 304
	PAYMENT_TIMEOUT_ERROR = 305
	PAYMENT_RESPONSE_ERROR = 306
	PAYMENT_AGE_GROUP_ERROR = 307
	PAYMENT_VALIDATION_ERROR = 308
	PAYMENT_AGE_OUT_RANGE_ERROR = 309
	PAYMENT_INVALID_BIRTH_DAY_ERROR = 310
	PAYMENT_PURCHASED_TIMES_ERROR = 311
	PAYMENT_PURCHASE_OVERTIME_ERROR = 312
	PAYMENT_PURCHASE_ALERT = 329
	SERIAL_CODE_NOT_RELEASE = 330
	SERIAL_CODE_INCOMPATIBLE = 331
	SERIAL_CODE_RESTRICTING = 332
	SERIAL_CODE_INVALID = 333
	SERIAL_CODE_LIMIT_OVER = 334
	SERIAL_CODE_TIME_LIMIT_OVER = 335
	SERIAL_CODE_CSV_ERROR = 336
	DATA_NOT_FOUND_ERROR = 500
	DATA_VALIDATION_ERROR = 501
	TRANSITION_OLD_ACCESS_ERROR = 516
	TRANSITION_COMPLETED_ERROR = 517
	INQUIRY_EMPTY_ERROR = 518
	INQUIRY_LENGTH_ERROR = 519
	USER_EXIST_ERROR = 520
	RECORD_EXIST_ERROR = 521
	DATA_REGISTER_ERROR = 522
	INVALID_PARAMETER_ERROR = 523
	USER_NOT_FOUND = 524
	CSV_ERROR = 525
	TRANSITION_USER_NOT_EXIST = 526
	TRANSITIONPASSWORD_INVALID = 700
	TRANSITION_USERID_INVALID = 701
	ACCOUNT_UDID_CONFLICT = 703
	NO_PLATFORM_USER_ID_ERROR = 705
	MAINTENANCE_TASK_ACCOUNT_SIGN_UP = 900
	MAINTENANCE_TASK_PRESENT = 901
	MAINTENANCE_TASK_DATA_LINKAGE = 902
	MAINTENANCE_TASK_ACCOUNT_CHAIN = 903
	MAINTENANCE_TASK_PAYMENT_ALL = 904
	MAINTENANCE_TASK_PAYMENT_IOS = 905
	MAINTENANCE_TASK_PAYMENT_ANDROID = 906
	MAINTENANCE_TASK_GACHA = 907
	MAINTENANCE_TASK_SHOP_ITEM_EXCHANGE = 908
	MAINTENANCE_TASK_EXCHANGE_BY_TICKET = 909
	MAINTENANCE_TASK_EXCHANGE_BY_MONEY = 910
	MAINTENANCE_TASK_EXCHANGE_BY_FRIEND_PT = 911
	MAINTENANCE_TASK_EXCHANGE_BY_COMMON_PIECE = 912
	MAINTENANCE_TASK_EXCHANGE_BY_GACHA_EXCHANGE = 913
	MAINTENANCE_TASK_EXCHANGE_BY_CIRCLE_PT = 914
	MAINTENANCE_TASK_EXCHANGE_BY_EXCHANGE_CURRENCY = 915
	MAINTENANCE_TASK_LIMITED_EXCHANGE = 916
	MAINTENANCE_TASK_SINGLE_MODE = 917
	MAINTENANCE_TASK_CIRCLE = 918
	MAINTENANCE_TASK_TEAM_STADIUM = 919
	MAINTENANCE_TASK_DAILY_RACE = 920
	MAINTENANCE_TASK_LEGEND_RACE = 921
	MAINTENANCE_TASK_MAIN_STORY = 922
	MAINTENANCE_TASK_CHARACTER_STORY = 923
	MAINTENANCE_TASK_CARD_TALENT_STRENGTHEN = 924
	MAINTENANCE_TASK_CARD_RARITY_UPGRADE = 925
	MAINTENANCE_TASK_CARD_UNLOCK = 926
	MAINTENANCE_TASK_SUPPORT_CARD_STRENGTHEN = 927
	MAINTENANCE_TASK_SUPPORT_CARD_LIMIT_BREAK = 928
	MAINTENANCE_TASK_SUPPORT_CARD_SELL = 929
	MAINTENANCE_TASK_TRAINED_CHARA_LOAD = 930
	MAINTENANCE_TASK_MISSION = 932
	MAINTENANCE_TASK_TEAM_EDIT = 933
	MAINTENANCE_TASK_TUTORIAL_TEAM_EDIT = 934
	MAINTENANCE_TASK_PAYMENT_DMM = 935
	MAINTENANCE_TASK_STORY_EVENT = 936
	MONEY_MAX_OVER_ERROR = 1001
	FRIENDPOINT_MAX_OVER_ERROR = 1002
	COIN_MAX_OVER_ERROR = 1003
	ITEM_MAX_OVER_ERROR = 1004
	CARD_MAX_OVER_ERROR = 1005
	USE_COIN_ERROR = 1051
	USE_TRAINER_POINT_ERROR = 1052
	NOT_ENOUGH_ERROR = 1053
	USE_MONEY_ERROR = 1054
	NOT_MATCH_VIEWER_ID = 1055
	SEARCH_USER_NOT_FOUND = 1056
	TUTORIAL_STEP_MISMATCH_ERROR = 1101
	TUTORIAL_OTHER_ACCESS_ERROR = 1102
	FRIEND_FOLLOW_COUNT_OVER_ERROR = 1451
	FRIEND_FOLLOW_USER_FOLLOW_COUNT_OVER_ERROR = 1452
	FRIEND_RENTAL_SUCCESSION = 1453
	MISSION_OVERTIME_ERROR = 1501
	MISSION_ROTATION_OVERTIME_ERROR = 1502
	PRESENT_NOT_RECEIVE_PRESENT = 1551
	PRESENT_NOT_RECEIVE_OVERDUE = 1552
	ITEM_EXCHANGE_ITEM_NOT_ENOUGH = 1601
	ITEM_EXCHANGE_LIMITED_EXCHANGE_EXPIRED = 1602
	GACHA_NOT_IN_TERM = 1801
	GACHA_LIMIT_ITEM_NOT_ENOUGH = 1802
	GACHA_UNSELECTABLE_CARD_SELECTED = 1803
	GACHA_LIMIT_ITEM_CEILING = 1804
	GACHA_DAILY_DRAW_END = 1805
	GACHA_FIRST_TIME_ONLY_DRAW_END = 1806
	GACHA_FREE_CAMPAIGN_NOT_AVAILABLE = 1807
	RACE_SIMULATOR_RESPONSE_ERROR = 2000
	RACE_SIMULATOR_CONNECT_ERROR = 2001
	RACE_SIMULATOR_CLIENT_ERROR = 2002
	RACE_SIMULATOR_PREFORKD_ERROR = 2003
	RACE_SIMULATOR_UNSUPPORTED_VERSION_ERROR = 2004
	LEGEND_RACE_NOT_RACE_TIME = 2101
	RACE_SIMULATE_VERSION_TOO_NEW = 2105
	RACE_SIMULATE_VERSION_TOO_OLD = 2106
	RACE_SINGLE_MODE_UNDEFINED_COMMAND_TYPE = 2501
	RACE_SINGLE_MODE_UNCHECKED_EVENT = 2502
	SINGLE_MODE_SUCCESSION_RENTAL_NOT_SAME_CIRCLE_MEMBER = 2503
	SINGLE_MODE_SUCCESSION_RENTAL_NUM_LIMIT = 2504
	SINGLE_MODE_SCENARIO_OUT_OF_TERM = 2505
	SINGLE_MODE_RENTAL_MONEY_NOT_ENOUGH = 2506
	TEAM_STADIUM_NOT_RACE_TIME = 2800
	TEAM_STADIUM_NOT_FOUND_TEAM = 2801
	CIRCLE_PENALTY_ERROR = 5001
	CIRCLE_MEMBER_NUM_ERROR = 5002
	CIRCLE_USER_REQUEST_COUNT_ERROR = 5003
	CIRCLE_REQUEST_COUNT_ERROR = 5004
	CIRCLE_SCOUT_COUNT_ERROR = 5005
	CIRCLE_CHAT_NO_JOIN_USER = 5006
	CIRCLE_ALREADY_JOIN = 5007
	CIRCLE_NOT_EXIST = 5008
	CIRCLE_NOT_BELONG = 5009
	CIRCLE_REQUEST_NOT_PERMITTED = 5011
	CIRCLE_ALREADY_SCOUT = 5012
	CIRCLE_NOT_MEMBER = 5014
	CIRCLE_NOT_OPERATE_TERM = 5015
	CIRCLE_NOT_REMOVE_TERM = 5016
	CIRCLE_NOT_SCOUT_TERM = 5017
	CIRCLE_ITEM_REQUEST_ERROR = 5020
	CIRCLE_DONATE_FAILED = 5021
	CIRCLE_ITEM_RECEIVE_ERROR = 5022
	CIRCLE_NO_OPERATION_AUTHORITY = 5023
	CIRCLE_SCOUT_MEMBER_MAX = 5024
	CIRCLE_NO_SCOUT_CIRCLE = 5025
	CIRCLE_NO_ITEM_REQUEST = 5026
	SAFETYNET_ERROR = 7001
	SAFETYNET_RETRY = 7002
	DEVICECHECK_ERROR = 8001
	CHAMPIONS_MATCHING_EMPTY = 8501
	CHAMPIONS_RESET_ENTRY_NUM = 8502
	CHAMPIONS_SCHEDULE_CHANGED = 8503
	STORY_EVENT_NOT_IN_TERM = 9001
	USER_NOT_FOUND_ON_LOGIN = 99999