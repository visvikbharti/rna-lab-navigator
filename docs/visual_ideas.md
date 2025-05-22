Below are **plug-and-play visual ideas**—one hero illustration plus two micro-animations—that will make RNA Lab Navigator feel polished and fun without slowing page loads. I’m giving you:

1. **Concept description** (what the asset conveys)
2. **Exact prompt** you can drop into DALL·E / Midjourney / Stable Diffusion (or hand to a designer)
3. **Implementation tip** (file format, size, where to place)

---

### 1 Landing-page hero illustration

|                    |                                                                                                                                                                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Concept**        | Cheerful lab “assistant sprite” (small floating robot) holding a stylised RNA double helix, sitting on a stack of PDF pages. The helix glows, pages show tiny citation marks. Background is a soft gradient in IGIB blue-green palette.     |
| **Prompt**         | > *“Friendly cartoon lab robot, silver and teal, holding glowing RNA double helix, sitting on stack of documents with citation symbols, soft gradient background, flat-vector style, clean lines, minimal shadows, 16:9, high resolution.”* |
| **Implementation** | Export as 1600 × 900 PNG (transparent background) and drop into the React `<HomePage>` header. Tailwind: `className="w-full max-h-[450px] object-contain"`                                                                                  |

---

### 2 Chat loading animation (Lottie)

|                    |                                                                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Concept**        | Three dots that morph into a rolling RNA helix while the answer is streaming.                                                                |
| **Prompt**         | Create or search LottieFiles: “RNA helix loading dots”. (If custom: illustrate three dots sliding, merge into helix, rotate 180°, loop 1 s.) |
| **Implementation** | Use `lottie-react` package:                                                                                                                  |

```jsx
import { Player } from "@lottiefiles/react-lottie-player";
<Player autoplay loop src="/lottie/helix_loader.json" style={{height: 60}} />
```

Place inside `ChatBox` while `isLoading` is true.

---

### 3 Protocol-uploaded confetti

|                    |                                                                                                                                        |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Concept**        | On successful PDF upload, trigger a 1-second burst of tiny page icons and RNA helices that fade quickly (micro-delight).               |
| **Prompt**         | Not an image—use **kernl/party.js** or **canvas-confetti**. Color tokens: `#3b82f6` (blue), `#10b981` (emerald), white document icons. |
| **Implementation** |                                                                                                                                        |

```js
import confetti from "canvas-confetti";
confetti({ particleCount: 40, spread: 55, origin: { y: 0.8 }});
```

Call inside `ProtocolUploader.jsx` after 201 response.

---

### Palette quick-ref

| Purpose           | Hex       |
| ----------------- | --------- |
| Primary blue      | `#2563eb` |
| Accent emerald    | `#10b981` |
| Background grey-0 | `#f9fafb` |
| Dark text         | `#1f2937` |

---

### Where to find ready Lottie files

* **Lottiefiles.com** keywords: *“science”, “molecule”, “microscope”, “data upload”*
* Filter by *CC BY 4.0* licence for safe internal use.
* File size < 400 KB keeps load snappy.

---

### Performance tip

* Convert hero PNG to **WebP**; defer-load with `loading="lazy"`.
* Keep Lottie JSON under 20 KB; use “compression” slider when exporting.
* Disable confetti on low-power mobile (`prefers-reduced-motion`).

---

Add these three touches and the app will feel **alive and purposeful** without overwhelming scientists who just need answers.
