var g=TycoonGameManager.Instance;
if(g.workers.Any(w=>w.ticketId>=0))throw new System.Exception("Wait for worker order to finish first");
int before=g.parts.Count;g.level=1;g.xp=1100;g.CloseDay();
if(g.level!=7||g.FlavorCount!=12||g.ToppingCount!=6||g.parts.Count!=before+10)throw new System.Exception("Multi-level rewards incorrect");
g.CloseDay();if(g.parts.Count!=before+10)throw new System.Exception("Day rewards duplicated");
float previous=5.3f;
for(int i=2;i<12;i++)
{
    float contribution=6+TycoonCatalogSO.Premiums[i]-TycoonCatalogSO.TubPrices[i]/24-.2f;
    if(contribution<=previous)throw new System.Exception("Later flavor does not increase profit");previous=contribution;
}
g.Save();
string result="At 1100 fixture XP, closing applied levels 2 through 7 exactly once: 12-flavor menu, six toppings, ten new empty cooled modules pending placement. Every later flavor has a higher contribution.";
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonProgression.txt",result);
return result;
