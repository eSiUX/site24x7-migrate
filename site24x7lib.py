#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, httplib, pprint, datetime, time

from logni import log

try:
        import json
        log.ni( 'use python module json', DBG=1 )

except ImportError:
        import simplejson as json
        log.ni( 'use python module simplejson as json', DBG=1 )



class Site24x7:

        def __init__(self, authToken):
                """
                 * Inicializace objektu pro praci se Site24x7 API
                 *
                 * @param authToken     autorizacni retezec
                 *
                """

                self.__authToken        = authToken
                self.__apiDomain        = 'www.site24x7.com'
                self.__apiPath          = '/api'



        def request( self, url='/monitors', paramList={}, method='GET' ):
                """
                 * Autorizovany request na pozadovana data
                 *
                 * @param url           URL pro data
                 * @param paramList     parametry requestu
                 * @param method        POST/GET/PUT, POST pro setovani, GET pro ziskani dat, PUT pro aktualizaci dat
                 * @return              slovnik s navratovym stavem + daty
                """

                ret = {
                        'statusCode'    : 200,
                        'statusMessage' : 'OK'
                }

                parList = urllib.urlencode(paramList)

                header = {
                       "Authorization" : "Zoho-authtoken %s" % self.__authToken,
                       "Accept"        : "application/json; version=2.0"
                }
                
                conUrl = "%s%s" % (self.__apiPath, url)

                log.ni("Site24x7 - url: %s, param: %s, header: %s", (conUrl, parList, header), INFO=3)

                connection = httplib.HTTPSConnection(self.__apiDomain)

                connection.request(method, conUrl, parList, header)

                response = connection.getresponse()

                status  = response.status
                data    = response.read()

                if status == 200:

                        data = json.loads(data)

                        # dotaz probehl v poradku, code != 0 indikuje chybu
                        if data['code'] == 0:
                                log.ni("Site24x7 - response - status: %s, data: %s", (status, data), INFO=3)

                                ret['data'] = data['data']
                        else:
                                log.ni("Site24x7 - response - code: %s, message: %s", ( data['code'], data['message'] ), ERR=4)

                                ret['statusCode']       = 500
                                ret['statusMessage']    = "code: %s - %s" % ( data['code'], data['message'] )
                else:
                        log.ni("Site24x7 - response - status: %s, data: %s", (status, data), ERR=4)

                        ret['statusCode']       = status
                        ret['statusMessage']    = data

                return ret
                


        def sourceList(self):
                """
                 * Vrati seznam merenych zdroju se zakladnim infem
                 *
                 * @return              slovnik s navratovym stavem + daty
                """

                ret = site.request('/monitors')

                if ret['statusCode'] != 200:
                        return ret

                data = []

                # prevodnik pro nektere typy zdroju
                # vsechny typy: https://www.site24x7.com/help/api/index.html#monitor-type-constants
                sourceType = {
                        'URL'           : 'http',
                        #'HOMEPAGE'      : 'selenium',
                        #'URL-SEQ'       : 'selenium',
                        'REALBROWSER'   : 'rum',
                        'PING'          : 'ping'
                }

                for monitor in ret['data']:
                        data.append({
                                'name'          : monitor['display_name'],
                                'id'            : monitor['monitor_id'],
                                'timeout'       : monitor['timeout'],
                                'url'           : monitor.get('website', ''),
                                'sourceType'    : sourceType.get(monitor['type'], '')
                        })

                ret['data'] = data

                return ret



        def sourceOutputInfo(self, date, monitorId):
                """
                 * Namerene hodnoty pro predany zdroj
                 *
                 * @param date          datum monitorovani, ISO format
                 * @param monitorId     ID zdroje
                 * @return              slovnik s navratovym stavem + daty
                """

                
                ret = self.request( '/reports/log_reports/%s?date=%s' % (monitorId, date) )

                if ret['statusCode'] != 200:
                        return ret

                reportList = ret['data'].get( 'report', [] )

                if not reportList:
                        ret['data'] = data
                        return

                data = {
                        'sender': [],
                        'output': []
                }

                for output in reportList:

                        collectionTime = output['collection_time'].split('+')[0]

                        checktime = datetime.datetime.strptime(collectionTime, "%Y-%m-%dT%H:%M:%S")

                        if checktime.strftime('%Y-%m-%d') != date:
                                continue
                
                        # casy jsou uvedeny v ms
                        data['output'].append({
                                'checktime'     : int( time.mktime( checktime.timetuple() ) ),
                                'connectTime'   : int( output['connection_time'] ) / 1000.0,
                                'resolveTime'   : int( output['dns_time'] ) / 1000.0,
                                'responseTime'  : int( output['response_time'] ) / 1000.0,
                                'outputLen'     : int( output['content_length'] ),
                                'statusMessage' : output['reason'],
                                'statusCode'    : int( output['response_code'] ),
                        })

                ret['data'] = data
 
                return ret



if __name__ == '__main__':

        log.mask( 'ALL' )
        log.stderr( 1 )

        site = Site24x7('17dd7fecf3944ae7644d21c33dcfe66d')

        #pprint.pprint( site.request('/monitors') )
        #pprint.pprint( site.request('/reports/log_reports/136657000000045544?date=2015-05-31') )
        #pprint.pprint( site.request('/notification_profiles') )
        #pprint.pprint( site.request('/email_templates') )
        #pprint.pprint( site.request('/monitor_groups') )
        #pprint.pprint( site.request('/users') )

        #pprint.pprint( site.sourceList() )
        pprint.pprint( site.sourceOutputInfo('2015-05-31', 136657000000045544) )
