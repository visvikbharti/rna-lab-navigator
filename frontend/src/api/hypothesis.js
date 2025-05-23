import config from './config';

/**
 * Explore a research hypothesis using advanced AI reasoning
 */
export const exploreHypothesis = async (question, useAdvancedModel = false) => {
  try {
    const response = await fetch(`${config.API_BASE_URL}/api/hypothesis/explore/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        use_advanced_model: useAdvancedModel,
        include_sources: true
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error exploring hypothesis:', error);
    throw error;
  }
};

/**
 * Generate a custom protocol based on requirements
 */
export const generateProtocol = async (requirements, baseProtocolId = null) => {
  try {
    const response = await fetch(`${config.API_BASE_URL}/api/hypothesis/generate-protocol/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        requirements,
        base_protocol_id: baseProtocolId,
        include_safety: true,
        format: 'structured'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error generating protocol:', error);
    throw error;
  }
};

/**
 * Get hypothesis mode status and available features
 */
export const getHypothesisStatus = async () => {
  try {
    const response = await fetch(`${config.API_BASE_URL}/api/hypothesis/status/`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error getting hypothesis status:', error);
    throw error;
  }
};