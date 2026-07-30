"""Agent implementations — production crew agents.

Exported agents (21 concrete agents + base + confirm helpers):
    BaseAgent, ScopeViolation
    CreativeReframing
    ConfirmSink protocol: TtyConfirmSink, AutoConfirmSink, ConfirmRequest, ConfirmResponse
    ResearchAgent
    ReferenceClusteringAgent
    MoodboardAgent
    StoryAgent
    ScriptAgent
    ShotDesignerAgent
    ShotPlanningAgent
    CharacterDirectorAgent
    StoryboardArtistAgent
    EnvironmentArtistAgent
    ReviewerAgent
    EditorAgent
    PublisherAgent
    VoiceDirectorAgent
    SoundDesignerAgent
    MusicComposerAgent
    ColoristAgent
    AnimationDirectorAgent
    AssetLibraryAgent
    GenerationAgent, MockGenerationPlugin, GenerationPlugin
"""
from agents.base import BaseAgent, ScopeViolation
from agents.creative_reframing import CreativeReframing
from agents.confirm_gate import TtyConfirmSink, AutoConfirmSink, ConfirmRequest, ConfirmResponse
from agents.research_agent import ResearchAgent
from agents.reference_clustering import ReferenceClusteringAgent
from agents.moodboard import MoodboardAgent
from agents.story import StoryAgent
from agents.script import ScriptAgent
from agents.shot_designer import ShotDesignerAgent
from agents.shot_planner import ShotPlanningAgent
from agents.character_director import CharacterDirectorAgent
from agents.storyboard_artist import StoryboardArtistAgent
from agents.environment_artist import EnvironmentArtistAgent
from agents.reviewer import ReviewerAgent
from agents.editor import EditorAgent
from agents.publisher import PublisherAgent
from agents.voice_director import VoiceDirectorAgent
from agents.sound_designer import SoundDesignerAgent
from agents.music_composer import MusicComposerAgent
from agents.colorist import ColoristAgent
from agents.animation_director import AnimationDirectorAgent
from agents.asset_library import AssetLibraryAgent
from agents.generation import GenerationAgent, MockGenerationPlugin, GenerationPlugin

__all__ = [
    "BaseAgent", "ScopeViolation",
    "CreativeReframing",
    "TtyConfirmSink", "AutoConfirmSink", "ConfirmRequest", "ConfirmResponse",
    "ResearchAgent",
    "ReferenceClusteringAgent",
    "MoodboardAgent",
    "StoryAgent",
    "ScriptAgent",
    "ShotDesignerAgent",
    "ShotPlanningAgent",
    "CharacterDirectorAgent",
    "StoryboardArtistAgent",
    "EnvironmentArtistAgent",
    "ReviewerAgent",
    "EditorAgent",
    "PublisherAgent",
    "VoiceDirectorAgent",
    "SoundDesignerAgent",
    "MusicComposerAgent",
    "ColoristAgent",
    "AnimationDirectorAgent",
    "AssetLibraryAgent",
    "GenerationAgent",
    "MockGenerationPlugin",
    "GenerationPlugin",
]