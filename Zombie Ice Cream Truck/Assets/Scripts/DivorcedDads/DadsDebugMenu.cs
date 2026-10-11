using Quantum;
using UnityEngine;
using UnityEngine.InputSystem;

// The debug menu: P shows the cheat list; while it is open, 1-9 send that cheat to the simulation (DadsCheatSystem)
// instead of switching hotbar slots.
public class DadsDebugMenu : MonoBehaviour
{
    [SerializeField] private DadsInput input;
    [SerializeField] private GameObject panel;

    private void Update()
    {
        var keyboard = Keyboard.current;
        if (keyboard.pKey.wasPressedThisFrame) panel.SetActive(!panel.activeSelf);
        input.MenuOpen = panel.activeSelf;
        if (!panel.activeSelf) return;
        for (int i = 0; i < 9; i++)
        {
            if (keyboard[Key.Digit1 + i].wasPressedThisFrame) QuantumRunner.Default.Game.SendCommand(new DadsCheat { Cheat = (Cheat)i });
        }
    }
}
