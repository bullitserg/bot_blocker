from ets.ets_mysql_lib import MysqlConnection as MyCn
from ets.ets_kaspersky_api_lib import KasperskyWorker
from ets.ets_cache_lib import CacheDict
from time import sleep
from config_parser import *
import logger_module
import queries


def trade_bot_blocker():
    # инициализируем логгер внутри функции, тогда он будет писать все от ее имени
    logger = logger_module.logger()

    # выполняем основной код
    try:
        logger.info('Searching bot started with threshold %s' % OFFER_THRESHOLD)
        bot_data_names = ['ip', 'offer_count', 'offer_per_second', 'last_offer', 'user_id', 'procedure_id']
        procedure_info = CacheDict(timeout=CACHE_TIMEOUT)
        user_info = CacheDict(timeout=CACHE_TIMEOUT)
        banned_bot_ip = []

        k_worker = KasperskyWorker()
        sql_44_db_cn = MyCn(connection=MyCn.MS_44_2_CONNECT)
        sql_log_db_cn = MyCn(connection=MyCn.MS_44_LOG_CONNECT)

        while True:
            # сначала добавим все адреса в бан, чтобы не тратить время на получение дополнительных данных
            # инициируем пустой список для ip, которые необходимо забанить в текушей итерации и для коллекции данных
            wait_ban_ip = []
            bot_info_collection = []

            # получаем данные о ботах
            with sql_log_db_cn.open():
                bot_data = sql_log_db_cn.execute_query(queries.bot_search_query, OFFER_THRESHOLD)

            if not bot_data:
                sleep(SLEEP_TIME)
                continue

            for bot in bot_data:
                # составляем словарь по конкретному боту
                bot_info = dict(zip(bot_data_names, bot))

                # Если адрес уже забанен, то пропускаем
                if bot_info['ip'] in banned_bot_ip:
                    continue

                # добавляем адрес в ожидающие блокирования
                wait_ban_ip.append(bot_info['ip'])
                bot_info_collection.append(bot_info)

            # если найдены ip для бана
            if wait_ban_ip:
                # добавляем адреса в blacklist
                # status, errors = k_worker.add_ip_list(wait_ban_ip, list_type='black')
                status, errors = True, False
                # если статус добавления True, то адреса забанены корректно
                if status:
                    logger.info('Addresses banned: %s' % ', '.join(wait_ban_ip))
                    banned_bot_ip += wait_ban_ip
                # если статус добавления False, то выводим в лог ошибку
                else:
                    logger.error('Banning error: %s' % str(errors))

                # теперь можем неспешно получить дополнительные данные и указать полные сведения об данных адресах в логе
                for bot_info in bot_info_collection:
                    # добавляем информацию о процедуре из procedure_info
                    if bot_info['procedure_id'] in procedure_info.keys():
                        bot_info['procedure_info'] = procedure_info['procedure_id']
                    # если в procedure_info сведения отсутствуют, то получаем запросом
                    else:
                        with sql_44_db_cn.open():
                            procedure_info['procedure_id'] = \
                                bot_info['procedure_info'] = \
                                sql_44_db_cn.execute_query(queries.procedure_info_query % bot_info['procedure_id'])[0][0]

                    # добавляем информацию об участнике из user_info
                    if bot_info['user_id'] in user_info.keys():
                        bot_info['user_info'] = user_info['user_id']
                    # если в user_info сведения отсутствуют, то получаем запросом
                    else:
                        with sql_44_db_cn.open():
                            user_info['user_id'] = \
                                bot_info['user_info'] = \
                                ' / '.join(sql_44_db_cn.execute_query(queries.user_info_query, bot_info['user_id'])[0])

                    # по каждому найденному боту пишем уведомление в лог
                    logger.info(
                        'Banned bot : %(offer_per_second)s offers in second from %(ip)-15s (%(procedure_info)s | %(user_info)s)' %
                        bot_info)

            # очищаем кэш от устаревших данных
            procedure_info.collect()
            user_info.collect()

            # ждем SLEEP_TIME до выполнения следующей итерации
            sleep(SLEEP_TIME)

    # если при исполнении будут исключения - кратко выводим на терминал, остальное - в лог
    except Exception as e:
        logger.fatal('Fatal error! Exit', exc_info=True)
        print('Critical error: %s' % e)
        print('More information in log file')
        exit(1)


if __name__ == '__main__':
    trade_bot_blocker()
