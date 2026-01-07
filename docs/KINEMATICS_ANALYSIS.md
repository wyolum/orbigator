# Kinematic Analysis: Ascending vs Descending

## Current Mapping (SGP4/Orbit Mode)
In `propagators.py`, the motors are driven as follows:
- **AoV (Angle of Vertical)** = Argument of Latitude ($u = \nu + \omega$)
- **EQX (Equinox)** = Longitude of Ascending Node ($\Omega - \text{GMST}$)

### AoV Ranges
- **$0^\circ - 180^\circ$**: Ascending Pass (Northbound crossing $\to$ North Apex $\to$ Southbound crossing). This creates the "Front" or "Ascending" arc.
- **$180^\circ - 360^\circ$**: Descending Pass (Southbound crossing $\to$ South Apex $\to$ Northbound crossing).

## Two Solutions for Static Targets
You are correct. If we implemented a mode to "Point to Latitude $L$", there are two valid mechanical configurations (assuming $|L| < i$):

1.  **Ascending Solution**:
    *   Set AoV to $u_1$ where $\sin(u_1) = \sin(L) / \sin(i)$ and $\cos(u_1) > 0$.
    *   Adjust EQX ring so the ascending node is to the West of the target.
    *   *Result*: The arm is in the "Front" ($0-90^\circ$) or just past it.
2.  **Descending Solution**:
    *   Set AoV to $u_2 = 180^\circ - u_1$.
    *   Adjust EQX ring so the descending node is to the West of the target.
    *   *Result*: The arm is in the "Back" ($90-180^\circ$ range of the sine wave, i.e. going down).

### Implication
For satellite tracking, the physics handles this automatically (the satellite is only at one spot at a time).
If we added a **"Point to City"** mode, we would need to choose one. "Ascending in Front" effectively means we'd prefer the solution where AoV $\in [0, 180]$ if possible (though for Southern hemisphere targets, we might need the "Descending" or "South" range).

## Mismatched Inclination Strategy
 **Hypothesis**: "As long as physical inclination ($i_{phys}$) is large enough, we can hit any lat/lon."

This is correct.
*   **Condition**: $i_{phys} \ge |Lat_{target}|$
*   **Implication**: We can track *any* satellite whose inclination $i_{sat} \le i_{phys}$.

### The Transformation (Virtual Inclination)
When $i_{phys} \ne i_{sat}$, the simple mapping ($AoV = u$, $EQX = \Omega$) breaks. We must compute explicit target angles:

Given target Satellite Lat $\phi_{sat}$ and Lon $\lambda_{sat}$ (relative to Earth-Fixed frame):

1.  **Solve for Arm Angle (AoV) $\theta$**:
    The height (sin Lat) is determined solely by the arm angle and physical inclination.
    $$\sin(\phi_{sat}) = \sin(i_{phys}) \cdot \sin(\theta)$$
    $$\theta = \arcsin\left(\frac{\sin(\phi_{sat})}{\sin(i_{phys})}\right)$$
    *Note: This gives two solutions for $\theta$ (Ascending vs Descending).*

2.  **Solve for Base Angle (EQX) $\psi$**:
    The arm's rotation contributes to the longitude. We need to find the longitude offset $\Delta\lambda_{arm}$ caused by the arm.
    $$\tan(\Delta\lambda_{arm}) = \cos(i_{phys}) \cdot \tan(\theta)$$
    The EQX motor must then rotate to place the node such that:
    $$EQX_{target} = \lambda_{sat} - \Delta\lambda_{arm}$$

This allows the Orbigator to act as a **Universal Tracker** for any orbit lower than its physical inclination.

## Definitions
**"Stored Inclination"**: The value currently stored in `orbigator_state.json` (variable `g.orbital_inclination_deg`).
*   **Role**: This acts as the **Physical Inclination** ($i_{phys}$) of the mechanism.
*   **Usage**: In Universal Tracker mode, this value is fixed by the hardware construction and used for the coordinate transformation, while the target's inclination comes from the TLE or target coordinates.
