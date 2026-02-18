
import { GoogleGenAI, Type } from "@google/genai";
import { AnalysisResult, Race, ReferenceObjectType, AnalysisMode } from "../types";
import { REFERENCE_OBJECTS } from "../constants";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const analyzeSheepImage = async (
  base64Image: string, 
  mode: AnalysisMode, 
  breedContext: Race, 
  refObjectId: ReferenceObjectType
): Promise<AnalysisResult> => {
  const model = "gemini-3-flash-preview";
  
  const refObject = REFERENCE_OBJECTS.find(o => o.id === refObjectId);
  const calibrationPrompt = refObject && refObject.id !== 'AUCUN' 
    ? `A REFERENCE CALIBRATION OBJECT IS IN THE PHOTO: ${refObject.label} (Known dimension: ${refObject.dimension}). Locate it and use it as a metric scale to provide high-precision measurements in CM.`
    : "No calibration object provided. Use standard breed proportions to estimate dimensions.";

  const analysisTask = mode === 'MAMMARY' ? `
    TASK: DETAILED MAMMARY EXAMINATION.
    1. Quantitative: Measure teat length, teat diameter, inter-teat distance in CM. Estimate udder volume.
    2. Qualitative: Assess Symmetry (Symétrique/Asymétrique), Attachment (Solide/Pendant), Shape (Globuleuse/Bifide), Teat Orientation (Verticale/Latérale).
    3. Global Mammary Score: 1 to 10.
  ` : `
    TASK: GENERAL MORPHOLOGY.
    1. Measure body length, wither height, heart girth, hip width in CM.
    2. Assess coat color and quality.
  `;

  const systemInstruction = `
    You are an expert Algerian Zootechnician and Veterinarian. 
    Analyze the provided image of a sheep (${breedContext} context).
    
    ${calibrationPrompt}
    ${analysisTask}
    
    Return the result in JSON format ONLY.
  `;

  const response = await ai.models.generateContent({
    model,
    contents: {
      parts: [
        { inlineData: { data: base64Image.split(',')[1], mimeType: "image/jpeg" } },
        { text: `Perform ${mode} analysis. Respond in JSON.` }
      ]
    },
    config: {
      systemInstruction,
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          race: { type: Type.STRING },
          robe_couleur: { type: Type.STRING },
          robe_qualite: { type: Type.STRING },
          measurements: {
            type: Type.OBJECT,
            properties: {
              longueur: { type: Type.NUMBER },
              hauteur: { type: Type.NUMBER },
              poitrine: { type: Type.NUMBER },
              bassin: { type: Type.NUMBER },
              profondeur: { type: Type.NUMBER },
              canon: { type: Type.NUMBER }
            }
          },
          mammary_traits: {
            type: Type.OBJECT,
            properties: {
              trayon_longueur: { type: Type.NUMBER },
              trayon_diametre: { type: Type.NUMBER },
              inter_trayon: { type: Type.NUMBER },
              volume_mammele: { type: Type.NUMBER },
              symetrie: { type: Type.STRING },
              attache: { type: Type.STRING },
              forme: { type: Type.STRING },
              orientation: { type: Type.STRING }
            }
          },
          mammary_score: { type: Type.NUMBER },
          classification: { type: Type.STRING },
          feedback: { type: Type.STRING }
        },
        required: ["race", "robe_couleur", "robe_qualite", "classification", "feedback"]
      }
    }
  });

  return JSON.parse(response.text);
};
