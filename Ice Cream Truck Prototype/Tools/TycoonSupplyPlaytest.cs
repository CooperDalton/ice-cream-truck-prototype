using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public static class TycoonSupplyPlaytest
{
    public static string[] Run()
    {
        var game = TycoonGameManager.Instance;
        var player = game.player;
        var inventory = player.inventory; var position = player.transform.position;
        float cash = game.cash; int level = game.level, selected = player.selected;
        var evidence = new List<string>();
        try
        {
            player.Teleport(game.supplier.position); game.level = 7;
            var products = new[] { 0, 12, 18, 19, 20, 21 };
            var kinds = new[] { TycoonItem.Kind.Tub, TycoonItem.Kind.Topping, TycoonItem.Kind.Bowls, TycoonItem.Kind.Batter, TycoonItem.Kind.ImprovedScooper, TycoonItem.Kind.BasicScooper };
            var amounts = new[] { 24, 30, 30, 20, 1, 1 };
            var prices = new[] { 12f, 6f, 6f, 12f, 12f, 6f };
            for (int i = 0; i < products.Length; i++)
            {
                player.inventory = new TycoonInventory(8); player.Select(0); game.cash = 100;
                int loose = game.looseItems.Count;
                if (!game.PurchaseSupply(products[i])) throw new Exception("Could not purchase " + kinds[i]);
                var items = player.inventory.slots.Where(item => item != null).ToArray();
                if (game.cash != 100 - prices[i] || items.Any(item => item.kind != kinds[i] || item.amount > item.Capacity) || items.Sum(item => item.amount) != amounts[i] || game.looseItems.Count != loose)
                    throw new Exception(kinds[i] + ": wrong charge, quantity, stack size, or delivery destination");
                evidence.Add(kinds[i] + ": " + amounts[i] + " usable portions/items in " + items.Length + " hotbar slots; charged " + prices[i] + "; no world package spawned.");
            }
            player.inventory = new TycoonInventory(8);
            for (int i = 0; i < 8; i++) player.inventory.slots[i] = new TycoonItem(TycoonItem.Kind.BasicScooper);
            game.cash = 100; string before = JsonUtility.ToJson(player.inventory);
            if (game.PurchaseSupply(18) || game.cash != 100 || JsonUtility.ToJson(player.inventory) != before)
                throw new Exception("Full hotbar purchase charged money or changed items");
            player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 10);
            before = JsonUtility.ToJson(player.inventory);
            if (game.PurchaseSupply(18) || game.cash != 100 || JsonUtility.ToJson(player.inventory) != before)
                throw new Exception("Purchase partially filled a stack before failing");
            player.inventory.slots[5] = player.inventory.slots[6] = player.inventory.slots[7] = null;
            if (!game.PurchaseSupply(18) || player.inventory.slots.Where(item => item != null && item.kind == TycoonItem.Kind.Bowls).Sum(item => item.amount) != 40)
                throw new Exception("Purchase did not use existing stack room and free slots correctly");
            evidence.Add("Full and partially-full hotbars reject purchases without charging or changing items; available stack room is used when the whole purchase fits.");
            player.inventory = new TycoonInventory(8); game.cash = 0;
            if (game.PurchaseSupply(19) || player.inventory.slots.Any(item => item != null)) throw new Exception("Insufficient cash still granted supplies");
            game.cash = 100; game.level = 1;
            if (game.PurchaseSupply(12) || game.cash != 100) throw new Exception("Locked topping could be purchased");
            evidence.Add("Cash and level restrictions still apply.");
            return evidence.ToArray();
        }
        finally
        {
            player.inventory = inventory; player.Select(selected); player.Teleport(position); game.cash = cash; game.level = level;
        }
    }
}
