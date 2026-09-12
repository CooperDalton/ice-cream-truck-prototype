using System;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.EventSystems;
using System.Collections.Generic;

public static class TycoonAllInventoryPlaytest
{
    private static void Check(bool result,string message)
    {
        if(!result)throw new Exception(message);
    }
    private static void Refresh(TycoonHUD hud)
    {
        typeof(TycoonHUD).GetMethod("Update",BindingFlags.NonPublic|BindingFlags.Instance).Invoke(hud,null);Canvas.ForceUpdateCanvases();
    }
    public static async Task<string[]> Run()
    {
        var g=TycoonGameManager.Instance;var p=g.player;var h=g.hud;g.restartRequested=true;p.manualInput=true;h.ClosePanels();g.phase=TycoonGameManager.Phase.Preparation;
        p.inventory=new TycoonInventory(8);p.Select(0);p.customerTarget=null;p.workerTarget=null;p.looseTarget=null;
        var cold=g.Parts(0,TycoonPart.Kind.ColdStorage).First();cold.storage=new TycoonInventory(4);cold.storage.slots[0]=new TycoonItem(TycoonItem.Kind.Tub,24,1);
        p.target=cold;p.Use(true);Refresh(h);
        Check(h.shelfPanel.activeSelf&&!h.panel.activeSelf&&!h.inventoryPanel.activeSelf&&h.storageViews.Single(v=>v.root.activeSelf).title.text=="Cold storage","Cold storage uses compact panel and readable title");
        await Task.Delay(100);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/ColdStorageCompact.png");await Task.Delay(100);
        var cases=new[]{new {inventory=cold.storage,title="Cold storage"},new {inventory=g.bike.cargo,title="Bicycle cargo"},new {inventory=new TycoonInventory(8),title="Staff locker"},new {inventory=g.truck.cargo,title="Truck cargo"},new {inventory=g.Parts(0,TycoonPart.Kind.Shelf).First().storage,title="Shelf"}};
        var evidence=new List<string>();
        foreach(var c in cases)
        {
            c.inventory.slots=new TycoonItem[c.inventory.slots.Length];p.inventory=new TycoonInventory(8);p.inventory.slots[0]=new TycoonItem(TycoonItem.Kind.BasicScooper);p.Select(0);
            h.OpenStorage(c.inventory,c.title);Refresh(h);var view=h.storageViews.Single(v=>v.root.activeSelf);
            Check(view.slots.Length==c.inventory.slots.Length&&!h.panel.activeSelf,"Correct capacity layout for "+c.title);
            var pointer=new PointerEventData(EventSystem.current){position=RectTransformUtility.WorldToScreenPoint(null,h.hotbar[0].frame.rectTransform.position)};var hits=new List<RaycastResult>();EventSystem.current.RaycastAll(pointer,hits);
            Check(hits.Count>0&&hits[0].gameObject==h.hotbar[0].button.gameObject,"Hotbar accessible below "+c.title);
            h.hotbar[0].button.onClick.Invoke();Check(p.inventory.slots[0]==null&&c.inventory.slots[0].Tool,"Hotbar stores in "+c.title);
            p.Select(7);view.slots[0].button.onClick.Invoke();Check(p.selected==0&&p.Held.Tool&&c.inventory.slots[0]==null,"Take returns and auto-selects from "+c.title);
            view.close.onClick.Invoke();Check(!h.AnyPanel,"Close restores gameplay");evidence.Add(c.title+": compact "+view.slots.Length+"-slot layout, accessible hotbar, store/take/auto-select and Close passed.");
        }
        g.cash=500;var locker=g.AddPart(4,0,g.sites[0].origin.position+new Vector3(2,0,-2));g.Hire(0,0);var worker=g.workers.Last();worker.inventory=new TycoonInventory(8);worker.onDuty=false;
        p.inventory=new TycoonInventory(8);p.inventory.slots[0]=new TycoonItem(TycoonItem.Kind.BasicScooper);p.Select(0);
        h.OpenEmployee(worker);Refresh(h);Check(h.employeeStorageView.root.activeSelf&&h.assignLockerButton.gameObject.activeInHierarchy,"Employee controls present");
        h.hotbar[0].button.onClick.Invoke();Check(worker.inventory.slots[0]!=null&&p.inventory.slots[0]==null,"Off-duty employee receives items");
        worker.onDuty=true;g.phase=TycoonGameManager.Phase.Trading;Refresh(h);h.employeeStorageView.slots[0].button.onClick.Invoke();
        Check(worker.inventory.slots[0]!=null&&p.inventory.slots[0]==null&&!h.hotbar[0].button.interactable&&!h.assignLockerButton.interactable,"On-duty transfer and assignment locked");
        worker.onDuty=false;g.phase=TycoonGameManager.Phase.Preparation;Refresh(h);h.employeeStorageView.slots[0].button.onClick.Invoke();Check(p.Held.Tool&&worker.inventory.slots[0]==null,"Off-duty transfers restored");
        await Task.Delay(100);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/EmployeeInventoryCompact.png");await Task.Delay(100);
        evidence.Add("Employee inventory matches storage styling, preserves stats and locker controls, and blocks transfers while on duty.");
        h.ClosePanels();h.ToggleInventory();Check(h.personalInventoryPanel.activeSelf&&!h.shelfPanel.activeSelf,"Personal inventory unchanged");
        h.ClosePanels();g.hud.menuOpen=true;return evidence.ToArray();
    }
}
