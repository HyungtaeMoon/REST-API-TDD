import time

from django.db.utils import OperationalError
from django.core.management import BaseCommand
from django.db import connections


class Command(BaseCommand):
    '''DB 를 사용할 수 있을 때까지 실행을 잠시 중지'''

    def handle(self, *args, **options):
        self.stdout.write('Wating for database...')
        db_conn = None
        while not db_conn:
            try:
                db_conn = connections['default']
            except OperationalError:
                self.stdout.write('데이터 베이스를 사용할 수 없으니 , 잠시만 기다려주세요(1초)...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('DB 를 사용할 수 있습니다.'))
