import { useProductionStore } from "../../store/productionStore"
import GuidedShell from "./shell/GuidedShell"
import { getStage } from "./data/stageMap"
import StateYourVisionStage from "./stages/StateYourVisionStage"
import PinYourReferencesStage from "./stages/PinYourReferencesStage"
import FindYourAngleStage from "./stages/FindYourAngleStage"
import BuildYourWorldStage from "./stages/BuildYourWorldStage"
import PlanTheProductionStage from "./stages/PlanTheProductionStage"
import GenerateAndPolishStage from "./stages/GenerateAndPolishStage"
import PublishWithEvidenceStage from "./stages/PublishWithEvidenceStage"

export default function GuidedFlow() {
  const flowStep = useProductionStore((s) => s.flowStep)
  const stage = getStage(flowStep)

  return (
    <GuidedShell>
      {stage.num === 1 ? <StateYourVisionStage />
      : stage.num === 2 ? <PinYourReferencesStage />
      : stage.num === 3 ? <FindYourAngleStage />
      : stage.num === 4 ? <BuildYourWorldStage />
      : stage.num === 5 ? <PlanTheProductionStage />
      : stage.num === 6 ? <GenerateAndPolishStage />
      : <PublishWithEvidenceStage />}
    </GuidedShell>
  )
}
