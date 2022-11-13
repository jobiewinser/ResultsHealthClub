import os
import glob
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import requests
import random as r
import json

class Command(BaseCommand):
    def handle(self, *args, **options):
        for _ in range(10):
            # url = f"/whatsapp-webhooks/"
            url = f"http://localhost:8083/whatsapp-webhooks/"
            ph_no = ""
            ph_no = ph_no + str(r.randint(6, 9))
            for i in range(1, 10):
                ph_no = ph_no + str(r.randint(0, 9))
                
            body = {
                "object": "whatsapp_business_account",
                "entry": [
                    {
                        "id": "1",
                        "changes": [
                            {
                                "field": "messages",
                                "value": {
                                    "messaging_product": "whatsapp",
                                    "metadata": {
                                        "display_phone_number": "447872000364",
                                        "phone_number_id": "123456123"
                                    },
                                    "contacts": [
                                        {
                                            "profile": {
                                                "name": "test user name"
                                            },
                                            "wa_id": "16315551181"
                                        }
                                    ],
                                    "messages": [
                                        {
                                            "from": ph_no,
                                            "id": "ABGGFlA5Fpa1",
                                            "timestamp": "2345936850",
                                            "type": "text",
                                            "text": {
                                                "body": "asdf"
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
            response = requests.post(url=url, json=body)