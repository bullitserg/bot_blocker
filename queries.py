bot_search_query = '''SELECT
  ip_data.remoteAddr,
  ip_data.cnt AS offerCount,
  CONVERT(ip_data.perc, char) AS offerPerSec,
  CONVERT(TIME(ip_data.last_offer_datetime), char) AS lastOffer,
  ip_data.userId,
  IFNULL(REPLACE(SUBSTR(a.uri, INSTR(a.uri, 'trade/offer/') + 12, 7), '/', ''), 0) AS procedureId
FROM (SELECT
    a.sessionId,
    a.userId,
    a.remoteAddr,
    MAX(UNIX_TIMESTAMP(a.dateTime)) - MIN(UNIX_TIMESTAMP(a.dateTime)) AS longer,
    MAX(a.dateTime) AS last_offer_datetime,
    COUNT(a.id) AS cnt,
    ROUND(COUNT(a.id) / (MAX(UNIX_TIMESTAMP(a.dateTime)) - MIN(UNIX_TIMESTAMP(a.dateTime))), 2) AS perc
  FROM httpActions a
  WHERE a.id > (SELECT
      MIN(a.id)
    FROM httpActions a
    WHERE a.dateTime > SUBDATE(NOW(), INTERVAL 15 MINUTE)) AND a.dateTime > (SELECT
      SUBDATE(MIN(a.dateTime), INTERVAL 15 MINUTE)
    FROM httpActions a) AND a.eventTypeId = 16 AND a.code = 200 -- /data/create-offer
  GROUP BY a.remoteAddr,
           a.userId,
           a.uri
  HAVING perc > %s AND longer > 10 AND last_offer_datetime > SUBDATE(NOW(), INTERVAL UNIX_TIMESTAMP(NOW()) - UNIX_TIMESTAMP((SELECT
      MAX(dateTime)
    FROM httpActions)) + 60 SECOND)
  ORDER BY perc DESC) AS ip_data
  LEFT JOIN httpActions a
    ON a.remoteAddr = ip_data.remoteAddr
    AND a.userId = ip_data.userId
    AND a.sessionId = ip_data.sessionId
    AND a.code = 200
    AND a.eventTypeId = 15 -- /trade/offer/NUMBER/
GROUP BY a.remoteAddr,
         a.userId,
         a.uri
ORDER BY lastOffer DESC;'''

procedure_info_query = '''SELECT
  p.registrationNumber
FROM procedures p
WHERE p.id = "%s"
  AND p.actualId IS NULL;'''

user_info_query = '''SELECT
  o.inn,
  u.username,
  CONCAT_WS(' ', u.lastName, u.firstName, u.middleName) AS user_fio
FROM user u
  JOIN organizationMember m
    ON m.userId = u.id
  JOIN organization o
    ON o.id = m.organizationId
WHERE u.id = "%s";'''