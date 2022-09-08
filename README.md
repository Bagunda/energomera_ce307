# energomera_ce307
Считывание показаний счётчика Энергомера CE307 R33.145.0A.N
Этот счётчик из полезных данных может выдавать только текущие показания киловатт*часов: суммарное, тариф1, тариф2, тариф3 (смотря сколько тарифов ночных, дневных и т.п.). Больше с него ничего не снять толкового!

Сверху на электросчётчике есть крышечка. У меня правый болтик опломбирован и он как раз нам не нужен.
Откручиваем левый болтик и за этот же край тянем и крышка открывается. И там нам доступны болтовые клемы для подключения по RS485.
Подключаем RS485 к клемам 12 (А) и 13 (В).
Подключаем питание 12В и не меньше 100мА к клемам 14 (GND) и 15 (+12В).
Внутри витой пары 4 пары скрученных проводочков. RS485 А и В должны идти по одной паре скрученных проводочков. Не добавляйте соседние проводочки на линию А и В! Иначе увеличивается площадь ловли помех и наводок. Например антенна 1кв.м. ловит 1дБ помех. А антенна 2кв.м. ловит 2дБ помех. 

Переходник USB - RS485 можно купить на али за пару сотен.
У меня такой:

![USB RS485](https://sun9-5.userapi.com/impg/1G-VXPO96-8arEcmEU5IkrfWwIUpvwPGyQSa9A/Bns312vzAcQ.jpg?size=220x200&quality=95&sign=cebfe2e8551e9c35723b3dabd7225ea4&type=album)

Потом лично я вставил этот переходник в Onion Omega2, который работает на линуксе и установил туда python3-lite.
Но другие скорее всего будут втыкать этот USB/RS485 в Raspberry pi, что более правильно и дешевле.
Но я хотел по WiFi передавать данные, чтобы малинка не была привязана проводами.

Из минусов.
1. Пакеты данных и запросов и ответов обрамлены байтом 0xC0. 0xC0 стоит и вначале пакета и в конце. Если в теле пакета встречается 0xC0, то его надо заменить 0xDB, 0xDC, но я это не делал. В пакете нет обычного окончания строки EOL типа \n и т.п. Поэтому не возможно воспользоваться функцией (readline). Читаем каждый пришедший байт, накапливаем и если пришёл 0xC0 и кол-во байт 16 и первая часть пакета равно C0 48 FD 00 96 34 57 01 30 00, то считываем значения киловатт
2. В ответе нет идентификации на какой запрос или на какой тариф пришёл ответ. Поэтому введены таймеры и запрашиваем по порядку потихоньку. И запрашиваем 2 раза для проверки.
3. В AdminTools (когда подключаешь USB-RS485 переходник к компьютеру), не вчитываясь внимательно в руководства - выбираешь канал связи "RS232 (CE30x)", что как бы логично. А надо выбирать "RS232 (CE102)".

Подключение надо настроить на скорость 9600 8N1.

Получив все данные я посылаю их по HTTP GET JSON в Home Assistant.
И программа закрывается.

В `crontab -e` я настроил расписание, чтобы программа запускалась каждый месяц 15го числа: `*/10 * * * * /usr/bin/python3 /root/schetchik.py`
