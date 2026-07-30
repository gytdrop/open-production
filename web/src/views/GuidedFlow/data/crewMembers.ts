import type { CrewMember } from "../types"

export const CREW: CrewMember[] = [
  { id: "creative_reframing",   name: "CreativeReframing",   role: "Proposes 3 creative angles (skeptic / advocate / contrarian).",   defaultStatus: "idle" },
  { id: "research_agent",       name: "ResearchAgent",       role: "Scans for prior work; enforces the >=3-source gate.",              defaultStatus: "idle" },
  { id: "reference_clustering", name: "ReferenceClustering", role: "Groups references, extracts style tokens, SHA-256 provenance.",   defaultStatus: "idle" },
  { id: "moodboard",            name: "Moodboard",           role: "Assembles the moodboard; locks the tone.",                         defaultStatus: "idle" },
  { id: "story",                name: "Story",               role: "Proposes story arc and structure.",                                defaultStatus: "idle" },
  { id: "script",               name: "Script",              role: "Proposes script lines, dialogue, narration.",                      defaultStatus: "idle" },
  { id: "character_director",   name: "CharacterDirector",   role: "Creates character profiles with consistency contracts.",          defaultStatus: "idle" },
  { id: "environment_artist",   name: "EnvironmentArtist",   role: "Proposes location specs and lighting presets.",                    defaultStatus: "idle" },
  { id: "shot_planner",         name: "ShotPlanning",        role: "Drafts scenes, shot list, and timing.",                           defaultStatus: "idle" },
  { id: "shot_designer",        name: "ShotDesigner",        role: "Camera and lighting specs per shot.",                              defaultStatus: "idle" },
  { id: "storyboard_artist",    name: "StoryboardArtist",    role: "ASCII blocking frames for each shot.",                             defaultStatus: "idle" },
  { id: "asset_library",        name: "AssetLibrary",        role: "Indexes every generated asset; reports gaps.",                     defaultStatus: "idle" },
  { id: "generation",           name: "Generation",          role: "Runs the multi-backend generation pass for a shot.",               defaultStatus: "idle" },
  { id: "animation_director",   name: "AnimationDirector",   role: "Animation pass on generated footage.",                             defaultStatus: "idle" },
  { id: "voice_director",       name: "VoiceDirector",       role: "Voice direction and synthesis per shot.",                          defaultStatus: "idle" },
  { id: "music_composer",       name: "MusicComposer",       role: "Music cue briefs per scene and timeline.",                         defaultStatus: "idle" },
  { id: "sound_designer",       name: "SoundDesigner",       role: "Sound palette (SFX + ambient) per scene.",                         defaultStatus: "idle" },
  { id: "colorist",             name: "Colorist",            role: "Color grade per shot, color look per scene.",                      defaultStatus: "idle" },
  { id: "editor",               name: "Editor",              role: "Cut assembly and timeline ordering.",                              defaultStatus: "idle" },
  { id: "reviewer",             name: "Reviewer",            role: "Validates every output against brief + consistency contract.",     defaultStatus: "idle" },
  { id: "publisher",            name: "Publisher",           role: "Generates publish manifests, runs final readiness gate.",           defaultStatus: "idle" },
]

export function getCrew(id: string): CrewMember | undefined {
  return CREW.find((c) => c.id === id)
}
