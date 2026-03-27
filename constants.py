from time_block import TimeBlock


BEGINNER = 0
INTERMEDIATE = 1
ADVANCED = 2
CLASS_LIMIT = 7
BLOCK_ONE = TimeBlock(800, 900)
BLOCK_TWO = TimeBlock(915, 1015)
BLOCK_THREE = TimeBlock(1045, 1145)
LUNCH_TIME = TimeBlock(1145, 1245)
BLOCK_FOUR = TimeBlock(1245, 1345)
BLOCK_FIVE = TimeBlock(1400, 1500)
BLOCK_SIX = TimeBlock(1530, 1630)
LEVEL_DICT = {
    BEGINNER: "Beginner",
    INTERMEDIATE: "Intermediate",
    ADVANCED: "Advanced"
}

TIME_BLOCKS = [BLOCK_ONE, BLOCK_TWO, BLOCK_THREE, BLOCK_FOUR, BLOCK_FIVE, BLOCK_SIX]

CORE_CLASSES = ["english", "math", "asl"]

def get_level(score: int):
    return 0 if score <= 3 else 2 if score > 6 else 1