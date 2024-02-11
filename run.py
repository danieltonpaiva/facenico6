#!/usr/bin/env python3

from facefusion import core
import os
from pyngrok import ngrok, conf
import fileinput
import sys
if __name__ == '__main__':
    Ngrok_token = "2bS14YWHhWE5Cjf57q1LGzL2zfH_fXfcBTG6sJqoQ7dKRi47"

    Ngrok_domain = "" # optional, leave empty if you don't have a domain




    if Ngrok_token!="":
        ngrok.kill()
        srv=ngrok.connect(7860 , pyngrok_config=conf.PyngrokConfig(auth_token=Ngrok_token),
                        bind_tls=True, domain=Ngrok_domain).public_url
        print(srv)
        core.cli()
    else:
        print('An ngrok token is required. You can get one on https://ngrok.com and paste it into the ngrok_token field.')
