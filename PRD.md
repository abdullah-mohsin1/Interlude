# Product Requirements Document (PRD)

## Project Name
Interlude AI

## Tagline
Ads that live inside the music

## Overview
Interlude AI is a prototype "fake Spotify" web app that demonstrates dynamic AI-generated, voice-matched ad segments inserted inside songs, blended to fit tone, rhythm, and energy.

## Goals
- Demonstrate seamless in-song ad insertion
- Show voice consistency using creator-consented voice cloning
- Provide modular architecture for rapid iteration
- Enable a fast, judge-friendly hackathon demo

## Non-Goals (MVP)
- Real Spotify integration
- Automated copyright handling
- Advanced singing synthesis
- Billing, analytics, and user accounts

## MVP Flow
1. User opens fake Spotify UI.
2. User selects a predefined song.
3. User enters an ad prompt.
4. User clicks generate.
5. Backend generates lyrics, generates voice (stub), mixes audio (stub), and returns output URL.
6. User toggles Original vs Modified playback.

## Required API
`POST /api/generate` with `{ song_id, ad_prompt }` returning `{ lyrics, audio_url }`.

## Config
Songs and insert windows are defined in `backend/config/songs.json`.

