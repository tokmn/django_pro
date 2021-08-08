import logging
from core_mq.mq import run_with_mq

logger = logging.getLogger(__name__)


class Priority:
    """
    MQ priority range: 1-10
    """
    LOWER = 1
    MIDDLE = 2
    HIGHER = 3
