import type { RoutineContent, RoutineData } from "../entities/types";

const mockRoutineData: RoutineData = {
  profile: {
    age: "22",
    skin_type: "Combination",
    concerns: ["Oiliness", "Dryness"],
  },
  warnings: [
    "Since you have combination skin, apply oil-control products only to your T-zone and hydrating products to dry cheeks.",
    "Patch test new products before full application.",
  ],
  morning_routine: [
    {
      step_number: 1,
      product_category: "Gentle Gel Cleanser",
      key_ingredients: ["Glycerin", "Panthenol"],
      usage_instructions:
        "Wash face with lukewarm water to remove night impurities without stripping moisture.",
      frequency: "daily",
    },
    {
      step_number: 2,
      product_category: "Serum",
      key_ingredients: ["Niacinamide", "Zinc"],
      usage_instructions:
        "Apply a few drops to the whole face to control oil and support the skin barrier.",
      frequency: "daily",
    },
    {
      step_number: 3,
      product_category: "Lightweight Gel-Cream",
      key_ingredients: ["Hyaluronic Acid", "Ceramides"],
      usage_instructions:
        "Apply a light layer to hydrate dry areas without making oily areas greasy.",
      frequency: "daily",
    },
    {
      step_number: 4,
      product_category: "Sunscreen SPF 30+",
      key_ingredients: ["Non-comedogenic filters"],
      usage_instructions:
        "Apply generously as the final step before makeup or going out.",
      frequency: "daily",
    },
  ],
  evening_routine: [
    {
      step_number: 1,
      product_category: "Micellar Water or Oil Cleanser",
      key_ingredients: ["Grape Seed Oil", "Jojoba Oil"],
      usage_instructions: "Gently remove sunscreen and sebum buildup.",
      frequency: "daily",
    },
    {
      step_number: 2,
      product_category: "Water-Based Foaming Cleanser",
      key_ingredients: ["Salicylic Acid (low concentration)"],
      usage_instructions: "Wash face thoroughly to clean pores.",
      frequency: "daily",
    },
    {
      step_number: 3,
      product_category: "BHA Toner",
      key_ingredients: ["Salicylic Acid"],
      usage_instructions:
        "Apply ONLY to the oily T-zone (forehead, nose, chin) with a cotton pad.",
      frequency: "2-3 times a week",
    },
  ],
  night_routine: [
    {
      step_number: 1,
      product_category: "Hydrating Serum",
      key_ingredients: ["Hyaluronic Acid", "Polyglutamic Acid"],
      usage_instructions: "Apply to damp skin to combat dryness on the cheeks.",
      frequency: "daily",
    },
    {
      step_number: 2,
      product_category: "Barrier Repair Moisturizer",
      key_ingredients: ["Ceramides", "Squalane"],
      usage_instructions:
        "Apply a slightly thicker layer to dry cheeks and a thin layer to the T-zone before sleep.",
      frequency: "daily",
    },
  ],
};

export const mockRoutineResponse: RoutineContent = {
  type: "routine",
  data: mockRoutineData,
};

export default mockRoutineData;
