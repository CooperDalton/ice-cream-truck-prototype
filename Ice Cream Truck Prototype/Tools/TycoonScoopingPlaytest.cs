using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public static class TycoonScoopingPlaytest
{
    public static string[] Run()
    {
        var game = TycoonGameManager.Instance;
        var player = game.player;
        var tub = game.Parts(0, TycoonPart.Kind.Tub).First();
        var inventory = player.inventory;
        var selected = player.selected;
        var manualInput = player.manualInput;
        var contents = tub.contents;
        var claim = tub.claimedBy;
        var target = player.target;
        var looseTarget = player.looseTarget;
        var workerTarget = player.workerTarget;
        var evidence = new List<string>();
        var completionFrames = new List<int>();
        try
        {
            player.manualInput = true;
            player.inventory = new TycoonInventory(8);
            player.looseTarget = null;
            player.workerTarget = null;
            tub.contents = new TycoonItem(TycoonItem.Kind.Tub, 12, tub.variant);
            tub.claimedBy = "";
            foreach (var kind in new[] { TycoonItem.Kind.BasicScooper, TycoonItem.Kind.ImprovedScooper })
            {
                player.inventory.slots[0] = new TycoonItem(kind);
                player.Select(0);
                player.target = tub;
                int stock = tub.contents.amount;
                player.Use(false);
                for (int i = 0; i < 20; i++) player.Gesture(new Vector2(30, 0), 1f / 60);
                if (player.gestureProgress != 0) throw new Exception(kind + ": horizontal movement added progress");
                player.Gesture(new Vector2(0, 3000), 1f / 60);
                float endpointProgress = player.gestureProgress;
                for (int i = 0; i < 60 && player.Held.loadedFlavor < 0; i++) player.Gesture(new Vector2(0, 30), 1f / 60);
                if (player.Held.loadedFlavor >= 0 || player.gestureProgress != endpointProgress || tub.contents.amount != stock)
                    throw new Exception(kind + ": continued one-way movement produced a scoop");
                player.CancelGesture();
                player.Use(false);
                if (player.gestureProgress != 0 || tub.contents.amount != stock) throw new Exception(kind + ": cancellation retained progress or spent stock");
                player.Gesture(new Vector2(0, -3000), 1f / 60);
                if (!Mathf.Approximately(player.gestureProgress, endpointProgress)) throw new Exception(kind + ": restarting did not recenter the stroke");
                endpointProgress = player.gestureProgress;
                for (int i = 0; i < 60 && player.Held.loadedFlavor < 0; i++) player.Gesture(new Vector2(0, -30), 1f / 60);
                if (player.Held.loadedFlavor >= 0 || player.gestureProgress != endpointProgress) throw new Exception(kind + ": downward movement bypassed the endpoint");
                player.CancelGesture();
                player.Use(false);
                player.Gesture(new Vector2(0, 90), 1f / 60);
                for (int i = 0; i < 40; i++) player.Gesture(Vector2.zero, 1f / 60);
                var front = player.grip.TransformPoint(new Vector3(0, .035f, -.111f));
                player.Gesture(new Vector2(0, -180), 1f / 60);
                for (int i = 0; i < 40; i++) player.Gesture(Vector2.zero, 1f / 60);
                var back = player.grip.TransformPoint(new Vector3(0, .035f, -.111f));
                if (Mathf.Abs(front.y - back.y) > .001f || Mathf.Abs(Vector3.Dot(back - front, tub.handTarget.forward) - .20f) > .001f)
                    throw new Exception(kind + ": scoop did not travel horizontally across the tub");
                if (Vector3.Distance((front + back) * .5f, tub.handTarget.position) > .001f)
                    throw new Exception(kind + ": bowl path is not centered on the ice cream surface");
                evidence.Add(kind + ": bowl traverses 0.20 m front-to-back at constant height, centered on the tub");
                player.CancelGesture();
                player.Use(false);
                for (int i = 0; i < 100 && player.Held.loadedFlavor < 0; i++) player.Gesture(new Vector2(0, i % 2 == 0 ? 3000 : -3000), .001f);
                if (player.Held.loadedFlavor >= 0) throw new Exception(kind + ": huge deltas bypassed minimum scooping time");
                player.CancelGesture();
                player.Use(false);
                int frames = 0;
                while (frames < 240 && player.Held.loadedFlavor < 0)
                {
                    player.Gesture(new Vector2(0, frames / 12 % 2 == 0 ? 15 : -15), 1f / 60);
                    frames++;
                }
                if (player.Held.loadedFlavor != tub.variant || tub.contents.amount != stock - 1)
                    throw new Exception(kind + ": alternating movement did not load exactly one scoop");
                completionFrames.Add(frames);
                evidence.Add(kind + ": one-way/horizontal movement blocked; cancellation resets; rapid deltas time-limited; alternating input completed in " + frames + " frames; stock " + stock + " -> " + tub.contents.amount);
            }
            if (completionFrames[1] >= completionFrames[0]) throw new Exception("Upgrade is not faster than the basic scooper");
            return evidence.ToArray();
        }
        finally
        {
            player.CancelGesture();
            player.inventory = inventory;
            player.Select(selected);
            player.manualInput = manualInput;
            player.target = target;
            player.looseTarget = looseTarget;
            player.workerTarget = workerTarget;
            tub.contents = contents;
            tub.claimedBy = claim;
        }
    }
}
