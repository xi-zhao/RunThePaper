# Lessons learned

1. **All numerical panels should share one physical state.** Using the same BEM
   resonance vector for the near and far fields makes the Fig. 6–7 relationship
   testable and prevents panel-specific fitting.
2. **Narrow resonances magnify mesh uncertainty.** Small changes in boundary
   discretization shift sparse peaks strongly, so Fig. 5 receives a strict
   pixel penalty even when the resonance sequence and physical checks agree.
3. **Dense images and sparse curves score differently.** The near-field panel
   reaches a much higher foreground score than the line plots; full-canvas
   similarity would hide this distinction behind white background.
4. **Undisclosed geometry is a real reproduction boundary.** The circular
   corner fillets and 432-element mesh are explicit approximations. They should
   not be presented as the paper's unavailable 1600-element discretization.
5. **Rendering optimization must not become physics fitting.** Canvas and line
   presentation can be tuned after arrays are frozen, while physical parameters
   and numerical samples remain immutable.
