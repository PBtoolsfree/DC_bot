"""Unit tests for AutoMod Services (Profanity, Link, Spam)."""

from unittest.mock import MagicMock

import discord
import pytest

from bot.database.schemas.automod import AutoModSettings, RuleConfig
from bot.services.automod.link_service import LinkService
from bot.services.automod.profanity_service import ProfanityService
from bot.services.automod.spam_service import SpamService
from bot.services.redis_service import RedisService


@pytest.fixture
def mock_message() -> MagicMock:
    msg = MagicMock(spec=discord.Message)
    msg.author = MagicMock(spec=discord.Member)
    msg.author.id = 123
    msg.author.bot = False
    msg.author.roles = []
    
    msg.channel = MagicMock(spec=discord.TextChannel)
    msg.channel.id = 456
    msg.channel.category_id = 789
    
    msg.guild = MagicMock(spec=discord.Guild)
    msg.guild.id = 1000
    
    msg.raw_mentions = []
    msg.raw_role_mentions = []
    msg.attachments = []
    return msg


@pytest.fixture
def base_settings() -> AutoModSettings:
    return AutoModSettings()


@pytest.mark.asyncio
class TestProfanityService:
    @pytest.fixture
    def service(self) -> ProfanityService:
        return ProfanityService()

    async def test_bad_words(self, service: ProfanityService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.words_profanity = RuleConfig(
            enabled=True,
            blacklist=["badword"]
        )
        
        # Test exact match
        mock_message.content = "this is a badword!"
        assert await service.check_message(mock_message, base_settings) == "words_profanity"
        
        # Test leetspeak bypass
        mock_message.content = "this is a b4dw0rd!"
        assert await service.check_message(mock_message, base_settings) == "words_profanity"

        # Test clean message
        mock_message.content = "this is clean"
        assert await service.check_message(mock_message, base_settings) is None

    async def test_regex(self, service: ProfanityService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.words_regex = RuleConfig(
            enabled=True,
            blacklist=[r"\b(?:badword|awful)\b"] # Case-insensitive by default in our engine
        )
        
        mock_message.content = "this is AWFUL"
        assert await service.check_message(mock_message, base_settings) == "words_regex"
        
        mock_message.content = "this is AwFuL"
        assert await service.check_message(mock_message, base_settings) == "words_regex"
        
        mock_message.content = "hello world"
        assert await service.check_message(mock_message, base_settings) is None

    async def test_zalgo(self, service: ProfanityService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.abuse_zalgo = RuleConfig(enabled=True, threshold=2)
        
        mock_message.content = "H\u0318\u034ee\u0317\u0323l\u0329\u032cl\u032d\u0326o"
        assert await service.check_message(mock_message, base_settings) == "abuse_zalgo"
        
        mock_message.content = "Hello"
        assert await service.check_message(mock_message, base_settings) is None


@pytest.mark.asyncio
class TestLinkService:
    @pytest.fixture
    def service(self) -> LinkService:
        return LinkService()

    async def test_discord_invites(self, service: LinkService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.links_invites = RuleConfig(enabled=True)
        
        mock_message.content = "Join my server: https://discord.gg/test1234"
        assert await service.check_message(mock_message, base_settings) == "links_invites"
        
        # Whitelisted invite
        base_settings.links_invites.whitelist = ["test1234"]
        assert await service.check_message(mock_message, base_settings) is None

    async def test_scam_domains(self, service: LinkService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.links_scam = RuleConfig(enabled=True, blacklist=["freediscordnitro.com"])
        
        mock_message.content = "Get nitro here: http://www.freediscordnitro.com/claim"
        assert await service.check_message(mock_message, base_settings) == "links_scam"

    async def test_external_whitelist(self, service: LinkService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        # Only allow github.com
        base_settings.links_external = RuleConfig(enabled=True, whitelist=["github.com"])
        
        mock_message.content = "Check my code: https://github.com/myrepo"
        assert await service.check_message(mock_message, base_settings) is None
        
        mock_message.content = "Check this out: https://youtube.com/watch"
        assert await service.check_message(mock_message, base_settings) == "links_external"


@pytest.mark.asyncio
class TestSpamService:
    @pytest.fixture
    def redis(self) -> RedisService:
        return RedisService() # InMemory fallback

    @pytest.fixture
    def service(self, redis: RedisService) -> SpamService:
        return SpamService(redis)

    async def test_caps_spam(self, service: SpamService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.spam_caps = RuleConfig(enabled=True, threshold=70) # >70% caps
        
        mock_message.content = "WHY IS EVERYONE IGNORING ME PLEASE HELP"
        assert await service.check_message(mock_message, base_settings) == "spam_caps"
        
        mock_message.content = "Hello there how are you?"
        assert await service.check_message(mock_message, base_settings) is None

    async def test_duplicate_messages(self, service: SpamService, mock_message: MagicMock, base_settings: AutoModSettings) -> None:
        base_settings.spam_duplicates = RuleConfig(enabled=True, threshold=3, cooldown_seconds=10)
        
        mock_message.content = "raid raid raid"
        
        # First 3 should pass
        assert await service.check_message(mock_message, base_settings) is None
        assert await service.check_message(mock_message, base_settings) is None
        assert await service.check_message(mock_message, base_settings) is None
        
        # 4th should trigger limit
        assert await service.check_message(mock_message, base_settings) == "spam_duplicates"
