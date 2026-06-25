import * as echarts from 'echarts/core'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

let registered = false

export function getEcharts() {
  if (!registered) {
    echarts.use([
      LineChart,
      PieChart,
      GridComponent,
      LegendComponent,
      TooltipComponent,
      CanvasRenderer,
    ])
    registered = true
  }
  return echarts
}
