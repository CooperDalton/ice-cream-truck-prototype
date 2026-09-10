return typeof(UnityEngine.AI.NavMesh).GetMethods().Where(m=>m.Name.Contains("Settings")).Select(m=>m.ToString()).ToArray();
