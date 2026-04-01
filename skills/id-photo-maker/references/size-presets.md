# Size Presets

首版优先支持常见中文证件照规格，并允许自定义毫米尺寸。

## Built-in photo presets

默认按 `300 DPI` 计算像素尺寸：

| key | aliases | physical size | pixel size @300dpi | notes |
| --- | --- | --- | --- | --- |
| `1-inch` | `1寸`, `一寸`, `1 inch` | `25 x 35 mm` | `295 x 413 px` | 常见一寸证件照 |
| `2-inch` | `2寸`, `二寸`, `2 inch` | `35 x 49 mm` | `413 x 579 px` | 常见两寸证件照 |
| `small-1-inch` | `小一寸`, `小1寸` | `22 x 32 mm` | `260 x 378 px` | 常见报名照 |
| `passport` | `护照`, `passport` | `33 x 48 mm` | `390 x 567 px` | 常见护照照规格 |

## Custom sizes

脚本接受两类自定义写法：

- 毫米：`35x45mm`
- 像素：`413x579px`

如果提供的是像素尺寸，脚本会按当前 `dpi` 反推毫米尺寸，方便打印排版。

## Background colors

支持以下命名色，也支持自定义十六进制颜色：

| value | output color |
| --- | --- |
| `white` | `#FFFFFF` |
| `blue` | `#438EDB` |
| `red` | `#D94B52` |
| `#RRGGBB` | custom |

## Framing presets

| key | aliases | behavior |
| --- | --- | --- |
| `standard` | `证件照`, `headshot`, `standard` | 标准近景证件照，默认值 |
| `half-body` | `半身照`, `half body` | 更保留肩颈和上半身 |
| `full-body` | `全身照`, `full body` | 定制排版，不是传统标准证件照 |

`full-body` 应被视为定制需求，而不是默认标准证件照规格。

## Print page presets

| key | physical size | default margin | default gap |
| --- | --- | --- | --- |
| `a4` | `210 x 297 mm` | `5 mm` | `2.5 mm` |
| `6inch` | `152 x 102 mm` | `4 mm` | `2 mm` |

脚本会按照真实物理尺寸自动计算一页能放下多少张。
