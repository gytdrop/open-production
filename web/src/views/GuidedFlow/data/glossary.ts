import type { GlossaryTerm } from "../types"

export const GLOSSARY: Record<number, GlossaryTerm[]> = {
  1: [
    { term: "Intent",   definition: "The user-supplied topic, audience, tone, and platform." },
    { term: "Topic",    definition: "A one-line brief of what the production is about." },
    { term: "Tone",     definition: "A descriptor for the emotional register (warm, neutral, tense, hopeful)." },
    { term: "Platform", definition: "Where the production will live (TikTok, Instagram, YouTube, Other)." },
  ],
  2: [
    { term: "Reference",   definition: "A piece of media (image, video, audio, text, url) that anchors the tone." },
    { term: "SHA-256",     definition: "A cryptographic hash that uniquely identifies a reference; immutable." },
    { term: "Provenance",  definition: "The origin and history of a piece of media. Required for every reference." },
    { term: "Style token", definition: "A named, reusable visual parameter extracted from a cluster of references." },
  ],
  3: [
    { term: "Skeptic",    definition: "The angle that surfaces objections to the mainstream framing." },
    { term: "Advocate",   definition: "The angle that argues the strongest case for the topic." },
    { term: "Contrarian", definition: "The non-obvious but defensible position." },
    { term: "Fit score",  definition: "The Reviewer\'s 0-100 alignment between the chosen angle and the brief." },
  ],
  4: [
    { term: "Character",            definition: "A named person in the story, with a consistency contract." },
    { term: "Environment",          definition: "A named location with lighting presets and visual anchors." },
    { term: "Consistency contract", definition: "Visual anchors the Reviewer uses to check every generated frame." },
    { term: "MoodSpec",             definition: "A locked tonal palette that downstream agents depend on." },
  ],
  5: [
    { term: "Scene",             definition: "A narrative unit containing a sequence of shots." },
    { term: "Shot",              definition: "A single camera setup with intent, duration, camera, lighting, audio." },
    { term: "Focal length",      definition: "Distance from lens to image plane; sets the field of view and compression." },
    { term: "Color temperature", definition: "Light warmth in Kelvin (3200K = warm, 5600K = daylight)." },
    { term: "Storyboard frame",  definition: "An ASCII blocking diagram of a shot, produced by StoryboardArtist." },
  ],
  6: [
    { term: "Pass",                definition: "A single specialist run inside the generation stage (frames, voice, music, etc.)." },
    { term: "Reviewer verdict",    definition: "pass / warn / fail for a single artifact, with severity score." },
    { term: "Backend",             definition: "The generation engine (runway-gen3, veo, local, mock)." },
    { term: "Blocking threshold",  definition: "A Reviewer score below which an artifact is not delivered to the user." },
  ],
  7: [
    { term: "Manifest",         definition: "A publication proposal: target platform, format, audience, gates." },
    { term: "Evidence gate",    definition: "A fail-closed check that all claims are sourced." },
    { term: "Consistency gate", definition: "A fail-closed check that the visual contract was honored throughout." },
    { term: "Publication gate", definition: "A fail-closed check that the production is ready for distribution." },
    { term: "Audit trail",      definition: "The append-only log of every decision, gate, and state change." },
  ],
}
