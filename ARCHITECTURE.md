# PetroNexa architecture

```text
                    +-----------------------------+
                    |  Flutter client              |
                    |  Android / iOS / Windows    |
                    |  macOS / Linux              |
                    +--------------+--------------+
                                   |
                               HTTPS/JSON
                                   |
                    +--------------v--------------+
                    | PetroNexa FastAPI           |
                    | auth / projects / reports   |
                    +--------------+--------------+
                                   |
             +---------------------+---------------------+
             |                                           |
   +---------v---------+                       +---------v---------+
   | Engineering Core  |                       | Data Layer        |
   | physics.py        |                       | SQLite local      |
   | cementing_engine  |                       | PostgreSQL cloud  |
   | gradients.py      |                       | users/projects    |
   | mud_parser.py     |                       +-------------------+
   +-------------------+
```

## Migration principle

The existing engineering calculations are preserved rather than rewritten. The Streamlit application remains available as a legacy/web interface while Flutter becomes the primary mobile/desktop UI.

## Current release scope

- Hydraulics API and Flutter screen
- Primary cementing API and Flutter screen
- JWT authentication
- User profile and project endpoints
- SQLite for local development
- PostgreSQL-ready async database URL
- PDF technical reporting
- Existing engineering unit tests retained

## Next engineering modules

1. Mud engineering and parser UI
2. Trajectory / MCM
3. Pressure-gradient window
4. Bit hydraulics and BHA/motor/MWD
5. Surge/swab and well control
6. Petrophysics
7. Reservoir/PVT
8. Production
9. Economics and field development
10. AI co-pilot with strict calculation provenance

Offline calculation should be added after the core Python equations are mirrored and independently validated in Dart. Do not silently approximate or duplicate engineering equations without cross-validation against the Python reference implementation.
