from django.db import models


class BailRequest(models.Model):
    # Represents a request for bail or fine payment (for Level 2 & 3 crimes)
    # Stores the amount determined by the Sergeant
    pass

class Reward(models.Model):
    # Represents a reward for a citizen who provided valid info
    # Stores the generated Unique ID and the calculated amount
    pass

class PaymentTransaction(models.Model):
    # Logs all financial transactions (connected to the Payment Gateway)
    # Tracks status (Success/Failed) for bails and rewards
    pass