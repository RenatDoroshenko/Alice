# Default app settings
SECRET_KEY = "tehoskrlachkisnateuhsanoeuh"
SAVE_TO_DB = True
DEFAULT_EXPERIENCE_SPACE = 1
TERMINAL_LOGS_ENABLED = True
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
MESSAGES_LIMIT_FROM_DB = 30
COMMANDS_ENABLED = False

# LLM Model
MODEL_ID = "gpt-3.5-turbo"
CONTEXT_TOKENS_LIMIT = 3000
MAX_TOKENS = 4096

# Long-term memory - General
LONG_MEMORY_ENABLED = True
MESSAGES_WITH_MEMORY_SHOWED_TO_AI = 2
RELEVANT_MEMORIES_TO_RETRIEVE = 3

# Long-term memory - embedding/index
EMBEDDING_MODEL = "text-embedding-ada-002"
FAISS_INDEX_FOLDER = "memory"
VECTOR_INDEX_DIMENSION = 1536

# Communication Modes
DEFAULT_COMMUNICATION_MODE = 'step_by_step'

# Show Messages
SHOW_THOUGHTS = True
SHOW_MEMORIES = True
SHOW_SYSTEM = True
