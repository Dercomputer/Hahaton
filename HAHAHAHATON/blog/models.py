from django.db import models


class offers_list(models.Model):
    json_data = models.TextField()


class correct_offer(models.Model):
    json_data2 = models.TextField()
