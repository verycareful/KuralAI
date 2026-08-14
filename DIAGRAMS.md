# Kural AI — UML & Architecture Diagrams

High-resolution PNG diagrams rendered directly from the source Mermaid code are available in the [`diagrams/`](file:///c:/Sricharan/GitHub/Kural%20AI/diagrams) directory:

- [**`workflow_diagram_16x9.png`**](file:///c:/Sricharan/GitHub/Kural%20AI/diagrams/workflow_diagram_16x9.png) — *Horizontal workflow diagram proportioned for 16:9 PPT slides*
- [**`uml_state_diagram.png`**](file:///c:/Sricharan/GitHub/Kural%20AI/diagrams/uml_state_diagram.png) — *UML State Machine Diagram (lifecycle & transition states)*
- [**`uml_sequence_diagram.png`**](file:///c:/Sricharan/GitHub/Kural%20AI/diagrams/uml_sequence_diagram.png) — *UML Sequence Diagram (interaction flow)*
- [**`uml_component_diagram.png`**](file:///c:/Sricharan/GitHub/Kural%20AI/diagrams/uml_component_diagram.png) — *UML Component & Subsystem Architecture Diagram*
- [**`uml_class_diagram.png`**](file:///c:/Sricharan/GitHub/Kural%20AI/diagrams/uml_class_diagram.png) — *UML Class & Module Structure Diagram*

---

## 1. End-to-End Workflow Diagram

Detailed state & data processing pipeline from raw Tamil text input to synthesized audiobook playback.

```mermaid
flowchart TD
    subgraph Client ["Frontend (Browser)"]
        A["User Inputs / Selects Tamil Text"] --> B["Click 'Generate Audiobook' (or Ctrl+Enter)"]
        B --> C["Disable Button & Show Spinner"]
        C --> D["POST /generate { text }"]
    end

    subgraph Backend_Flask ["Flask Server (app.py)"]
        D --> E["Validate Request (length, empty check)"]
        E --> F["Invoke tagger.tag_text(text)"]
    end

    subgraph NLP_Tagger ["NLP Tagger (tagger.py)"]
        F --> G["Normalize Whitespace"]
        G --> H["Regex Dialogue Extraction<br/>(Smart quotes, ASCII quotes, Guillemets)"]
        H --> I["Segment Text into Narration & Dialogue blocks"]
        I --> J["Gender Attribution & Character Tracking<br/>(Morphology: என்றார், கேட்டாள், முருகன், வசந்தா...)"]
        J --> K["Assign Gender-Consistent Voices & Persistent Character IDs"]
        K --> L["Word-Boundary Navarasa Emotion Detection<br/>(Angry, Fear, Sad, Surprise, Happy, Tender, Punctuation)"]
        L --> M["Calculate Prosody Modulation (Rate: ±15%, Pitch: ±10Hz, Volume: ±15%)"]
        M --> N["Produce List of Segment Objects"]
    end

    subgraph Audio_Pipeline ["Audio Pipeline (pipeline.py)"]
        N --> O["Invoke pipeline.generate(segments)"]
        O --> P["Create Isolated Temp Directory"]
        P --> Q["Async Synthesis Loop (edge-tts Communicate)"]
        Q --> R["Generate seg_0000.mp3, seg_0001.mp3..."]
        R --> S["Load MP3s into pydub AudioSegments"]
        S --> T{"Speaker Change?"}
        T -- "Yes (Different Speaker)" --> U["Insert 450ms Silence"]
        T -- "No (Same Speaker)" --> V["Insert 200ms Silence"]
        U --> W["Stitch Segments Consecutively"]
        V --> W
        W --> X["Export Final MP3 to output/UUID.mp3"]
        X --> Y["Clean up Temp Directory"]
    end

    subgraph Response_And_Playback ["Delivery & UI Rendering"]
        Y --> Z["Return JSON { audio_url, segments }"]
        Z --> AA["Render Staggered Tagged Segments View"]
        Z --> AB["Load & Autoplay Audio via &lt;audio&gt; element"]
        Z --> AC["Enable Download MP3 Button"]
    end
```

---

## 2. UML Sequence Diagram

Runtime interactions between the Client, Flask API, NLP Tagger, Audio Pipeline, and External Edge TTS Cloud Service.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Browser (index.html)
    participant Flask as Flask Server (app.py)
    participant Tagger as NLP Tagger (tagger.py)
    participant Pipeline as Pipeline (pipeline.py)
    participant EdgeTTS as Microsoft Edge Neural TTS
    participant Pydub as PyDub / FFmpeg
    participant Storage as Local Storage (output/)

    User->>UI: Selects example / inputs Tamil text
    User->>UI: Clicks "Generate Audiobook"
    UI->>UI: Set loading state (spinner active)
    UI->>Flask: POST /generate { text: "..." }
    
    activate Flask
    Flask->>Tagger: tag_text(text)
    activate Tagger
    Tagger->>Tagger: Split dialogue & narration
    Tagger->>Tagger: Match speaker attribution
    Tagger->>Tagger: Match emotion keywords & rate
    Tagger-->>Flask: Return List[Segment]
    deactivate Tagger

    Flask->>Pipeline: generate(segments)
    activate Pipeline
    Pipeline->>Pipeline: Create temp directory

    loop For each Segment (concurrent/async)
        Pipeline->>EdgeTTS: Communicate(text, voice, rate)
        activate EdgeTTS
        EdgeTTS-->>Pipeline: Stream MP3 audio
        deactivate EdgeTTS
        Pipeline->>Pipeline: Save temp seg_i.mp3
    end

    loop For each synthesized segment
        Pipeline->>Pydub: Load temp MP3
        alt Speaker changed
            Pipeline->>Pydub: Append 450ms silence
        else Same speaker
            Pipeline->>Pydub: Append 200ms silence
        end
        Pipeline->>Pydub: Append AudioSegment
    end

    Pipeline->>Pydub: Export combined audio as MP3
    Pydub->>Storage: Write output/{uuid}.mp3
    Pipeline->>Pipeline: Delete temp files
    Pipeline-->>Flask: Return (filename, segment_dicts)
    deactivate Pipeline

    Flask-->>UI: 200 OK { audio_url: "/output/{id}.mp3", segments: [...] }
    deactivate Flask

    UI->>UI: Render color-coded segment badges
    UI->>Storage: Fetch /output/{id}.mp3
    Storage-->>UI: Audio binary stream
    UI->>User: Play multi-voice audio & show download button
```

---

## 3. UML Component Diagram

High-level architectural components, boundaries, and dependencies.

```mermaid
componentDiagram
    package "Client Tier" {
        [Vanilla Web UI] as UI
        [Audio Player Component] as Player
        [Segment Visualizer] as Visualizer
        [Example Selector] as Selector
    }

    package "Application Tier (Flask)" {
        [HTTP Routing & REST API] as API
        [Static File Server] as StaticServer
    }

    package "Core Engine" {
        [Regex NLP Tagger] as Tagger
        [Audio Stitching Pipeline] as Pipeline
        [Curated Examples Repository] as Examples
    }

    package "External Services & System Libraries" {
        cloud "Microsoft Edge Neural TTS" as CloudTTS
        [PyDub Audio Processing] as Pydub
        [FFmpeg Engine] as FFmpeg
    }

    database "File System" {
        folder "/output (MP3s)" as OutputStorage
        folder "/static (HTML/CSS/JS)" as StaticStorage
    }

    UI --> API : POST /generate
    UI --> API : GET /voices, /examples
    StaticServer --> StaticStorage : Serves index.html
    API --> Tagger : Passes raw text
    API --> Pipeline : Passes tagged segments
    API --> Examples : Queries sample passages
    API --> OutputStorage : Serves generated MP3s
    
    Pipeline ..> CloudTTS : edge_tts.Communicate()
    Pipeline ..> Pydub : Audio concatenation & pauses
    Pydub ..> FFmpeg : Transcoding & stitching
    Pipeline --> OutputStorage : Writes .mp3 files
```

---

## 4. UML Class Diagram

Data structures, types, module boundaries, and relationships.

```mermaid
classDiagram
    class Segment {
        +str text
        +str seg_type
        +int speaker_id
        +str emotion
        +str rate
        +to_dict() dict
    }

    class Voice {
        +int id
        +str name
        +str label
        +str gender
        +str accent
    }

    class TaggerModule {
        <<module: tagger.py>>
        +List~Voice~ VOICES
        +dict EMOTION_RATE
        +List~str~ SAD_KEYWORDS
        +List~str~ ANGRY_KEYWORDS
        +List~str~ HAPPY_KEYWORDS
        +List~str~ FEAR_KEYWORDS
        +List~str~ SURPRISE_KEYWORDS
        +List~str~ TENDER_KEYWORDS
        +List~str~ ATTRIBUTION_VERBS
        +tag_text(text: str) List~Segment~
        -_split_into_raw_segments(text: str) List~dict~
        -_assign_speakers(raw_segments: List~dict~) List~dict~
        -detect_emotion(text: str) str
        -_keyword_in_text(keyword: str, text: str) bool
    }

    class PipelineModule {
        <<module: pipeline.py>>
        +int SPEAKER_CHANGE_PAUSE_MS = 450
        +int SAME_SPEAKER_PAUSE_MS = 200
        +str OUTPUT_DIR
        +generate(segments: List~Segment~) Tuple~str, List~dict~~
        -_generate_async(segments: List~Segment~) Tuple~str, List~dict~~
        -_synthesize_segment(segment: Segment, path: str) str
        +ensure_output_dir() void
    }

    class ExamplesModule {
        <<module: examples.py>>
        +List~dict~ EXAMPLES
        +get_example_by_id(example_id: str) dict
        +get_all_titles() List~dict~
    }

    class FlaskApp {
        <<module: app.py>>
        +index() Response
        +generate_audio() Response
        +get_voices() Response
        +list_examples() Response
        +get_example(example_id: str) Response
        +serve_output(filename: str) Response
    }

    TaggerModule ..> Segment : creates
    TaggerModule ..> Voice : uses
    PipelineModule ..> Segment : processes
    FlaskApp --> TaggerModule : invokes
    FlaskApp --> PipelineModule : invokes
    FlaskApp --> ExamplesModule : queries
```

---

## 5. UML State Machine Diagram

State transitions and lifecycle events across the ingestion, NLP parsing, voice dispatch, neural synthesis, pause injection, and audio delivery stages.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Ingestion : POST /generate

    state Ingestion {
        [*] --> ValidatePayload
        ValidatePayload --> CheckEncoding : UTF-8 & Bounds
        CheckEncoding --> ParseNarrator : Choosable Voice
        ParseNarrator --> [*]
    }

    Ingestion --> NLPTagging : Raw Text

    state NLPTagging {
        [*] --> QuoteSegmentation : Smart / ASCII / Guillemets
        QuoteSegmentation --> SpeakerAttribution : Attribution Verbs
        SpeakerAttribution --> EmotionDetection : 65+ Navarasa Lexicon
        EmotionDetection --> ProsodyCalculation : Rate (-15% to +15%)
        ProsodyCalculation --> [*]
    }

    NLPTagging --> VoiceDispatch : List[Segment]

    state VoiceDispatch {
        [*] --> BindNarrator : Speaker 0 -> Narrator
        BindNarrator --> BindCharacters : Speakers 1..7 -> Cast Pool
        BindCharacters --> [*]
    }

    VoiceDispatch --> AudioSynthesis : Tagged Stream

    state AudioSynthesis {
        [*] --> AsyncTTSWorker : edge_tts.Communicate()
        AsyncTTSWorker --> StreamMP3 : Concurrent Tasks
        StreamMP3 --> StoreTempBuffers : seg_0000.mp3 ... seg_N.mp3
        StoreTempBuffers --> [*]
    }

    AudioSynthesis --> AudioStitching : Raw MP3 Chunks

    state AudioStitching {
        [*] --> TransitionCheck
        state TransitionCheck <<choice>>
        TransitionCheck --> Pause450ms : Speaker Changed
        TransitionCheck --> Pause200ms : Same Speaker
        Pause450ms --> ConcatAudio : PyDub
        Pause200ms --> ConcatAudio : PyDub
        ConcatAudio --> ExportMaster : output/UUID.mp3
        ExportMaster --> [*]
    }

    AudioStitching --> WebDelivery : Master MP3

    state WebDelivery {
        [*] --> SendJSON : 200 OK Response
        SendJSON --> RenderUI : Color-Coded Inspector
        RenderUI --> PlayAudio : HTML5 Autoplay
        PlayAudio --> [*]
    }

    WebDelivery --> [*] : Done
```

