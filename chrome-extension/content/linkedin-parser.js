// LinkedIn Parser Module
// Specialized functions for extracting data from LinkedIn's DOM structure

const LinkedInParser = {
  // Main extraction function
  parseProfile() {
    return {
      basic: this.extractBasicInfo(),
      experience: this.extractDetailedExperience(),
      education: this.extractDetailedEducation(),
      skills: this.extractDetailedSkills(),
      certifications: this.extractCertifications(),
      languages: this.extractLanguages(),
      recommendations: this.extractRecommendations(),
      profileStrength: this.extractProfileStrength()
    };
  },

  // Extract basic profile information
  extractBasicInfo() {
    return {
      name: this.extractName(),
      headline: this.extractHeadline(),
      location: this.extractLocation(),
      industry: this.extractIndustry(),
      connections: this.extractConnectionCount(),
      profilePicture: this.extractProfilePicture(),
      backgroundImage: this.extractBackgroundImage(),
      about: this.extractAbout(),
      contactInfo: this.extractContactInfo()
    };
  },

  // Enhanced name extraction
  extractName() {
    const selectors = [
      'h1.text-heading-xlarge',
      '.pv-text-details__left-panel h1',
      'h1[class*="inline t-24"]',
      '.pv-top-card__title',
      'h1.pv-top-card-section__name',
      '[data-generated-suggestion-target] h1'
    ];

    return this.trySelectors(selectors);
  },

  // Enhanced headline extraction
  extractHeadline() {
    const selectors = [
      '.text-body-medium.break-words',
      'div.text-body-medium.break-words',
      '.pv-text-details__left-panel:nth-child(2)',
      '.pv-top-card-section__headline',
      'h2.mt1.t-18'
    ];

    return this.trySelectors(selectors);
  },

  // Extract location
  extractLocation() {
    const selectors = [
      '.pv-text-details__left-panel > span:first-of-type',
      '.text-body-small.inline.t-black--light.break-words',
      'span[class*="text-body-small inline"]',
      '.pv-top-card-section__location'
    ];

    const location = this.trySelectors(selectors);

    // Clean up location string
    if (location) {
      return location.replace(/[\n\s]+/g, ' ').trim();
    }

    return null;
  },

  // Extract industry
  extractIndustry() {
    const aboutSection = document.querySelector('#about');
    if (aboutSection) {
      const parent = aboutSection.closest('section');
      const industryText = parent?.querySelector('.text-body-small.t-black--light');
      if (industryText) {
        return industryText.textContent.trim();
      }
    }
    return null;
  },

  // Extract connection count
  extractConnectionCount() {
    const selectors = [
      '.pv-top-card--list-bullet .t-black--light span',
      'span:contains("connections")',
      '.pv-top-card__connections span'
    ];

    const text = this.trySelectors(selectors);
    if (text) {
      const match = text.match(/(\d+[\d,]*)\+?\s*connection/i);
      if (match) {
        return match[1].replace(/,/g, '');
      }
    }

    return null;
  },

  // Extract profile picture URL
  extractProfilePicture() {
    const selectors = [
      '.pv-top-card-profile-picture__image',
      '.profile-photo-edit__preview',
      'img.pv-top-card__photo',
      '.presence-entity__image'
    ];

    const img = document.querySelector(selectors.join(', '));
    return img ? img.src : null;
  },

  // Extract background image URL
  extractBackgroundImage() {
    const selectors = [
      '.profile-background-image__image',
      '.pv-top-card__background-image',
      '[class*="profile-background-image"] img'
    ];

    const img = document.querySelector(selectors.join(', '));
    return img ? img.src : null;
  },

  // Extract about section with full text
  extractAbout() {
    const aboutSection = document.querySelector('#about');
    if (aboutSection) {
      const parent = aboutSection.closest('section');
      const aboutText = parent?.querySelector('[class*="inline-show-more-text"]');

      if (aboutText) {
        // Click "see more" if available
        const seeMoreBtn = aboutText.querySelector('button[aria-label*="more"]');
        if (seeMoreBtn) {
          seeMoreBtn.click();
          // Wait a bit for expansion
          setTimeout(() => {}, 100);
        }

        return aboutText.textContent.trim();
      }
    }

    return null;
  },

  // Extract contact information
  extractContactInfo() {
    const contactInfo = {};

    // Try to find contact info section
    const contactSection = document.querySelector('[href*="/overlay/contact-info/"]');
    if (contactSection) {
      // This would require clicking and waiting, so we mark it as available
      contactInfo.available = true;
    }

    // Extract public email if visible
    const emailLink = document.querySelector('a[href^="mailto:"]');
    if (emailLink) {
      contactInfo.email = emailLink.href.replace('mailto:', '');
    }

    // Extract website
    const websiteLink = document.querySelector('.pv-contact-info__contact-type a[href*="http"]');
    if (websiteLink) {
      contactInfo.website = websiteLink.href;
    }

    return Object.keys(contactInfo).length > 0 ? contactInfo : null;
  },

  // Extract detailed experience
  extractDetailedExperience() {
    const experiences = [];
    const experienceSection = document.querySelector('#experience');

    if (!experienceSection) {
      return experiences;
    }

    const parent = experienceSection.closest('section');
    const items = parent?.querySelectorAll('.pvs-list__paged-list-item');

    items?.forEach(item => {
      const experience = {};

      // Extract role/title
      const titleElement = item.querySelector('[class*="t-bold"] span[aria-hidden="true"]');
      if (titleElement) {
        experience.title = titleElement.textContent.trim();
      }

      // Extract company name and employment type
      const companyElement = item.querySelector('.t-14.t-normal:not(.t-black--light) span[aria-hidden="true"]');
      if (companyElement) {
        const companyText = companyElement.textContent.trim();
        const parts = companyText.split('·');
        experience.company = parts[0].trim();
        if (parts[1]) {
          experience.employmentType = parts[1].trim();
        }
      }

      // Extract duration
      const durationElement = item.querySelector('.t-14.t-normal.t-black--light span[aria-hidden="true"]');
      if (durationElement) {
        const durationText = durationElement.textContent.trim();
        const durationParts = durationText.split('·');
        experience.dateRange = durationParts[0].trim();
        if (durationParts[1]) {
          experience.duration = durationParts[1].trim();
        }
      }

      // Extract location
      const locationElements = item.querySelectorAll('.t-14.t-normal.t-black--light span[aria-hidden="true"]');
      locationElements.forEach(elem => {
        const text = elem.textContent.trim();
        if (text.includes(',') && !text.includes('·') && !text.includes('yr') && !text.includes('mo')) {
          experience.location = text;
        }
      });

      // Extract description
      const descriptionElement = item.querySelector('.pvs-list__outer-container > ul');
      if (descriptionElement) {
        const bulletPoints = [];
        descriptionElement.querySelectorAll('li').forEach(li => {
          const text = li.textContent.trim();
          if (text) {
            bulletPoints.push(text);
          }
        });
        if (bulletPoints.length > 0) {
          experience.description = bulletPoints.join('\n');
        }
      }

      // Extract company logo
      const logoImg = item.querySelector('img[class*="EntityPhoto"]');
      if (logoImg) {
        experience.companyLogo = logoImg.src;
      }

      // Only add if we have at least a title
      if (experience.title) {
        experiences.push(experience);
      }
    });

    return experiences;
  },

  // Extract detailed education
  extractDetailedEducation() {
    const education = [];
    const educationSection = document.querySelector('#education');

    if (!educationSection) {
      return education;
    }

    const parent = educationSection.closest('section');
    const items = parent?.querySelectorAll('.pvs-list__paged-list-item');

    items?.forEach(item => {
      const edu = {};

      // Extract school name
      const schoolElement = item.querySelector('[class*="t-bold"] span[aria-hidden="true"]');
      if (schoolElement) {
        edu.school = schoolElement.textContent.trim();
      }

      // Extract degree and field of study
      const degreeElement = item.querySelector('.t-14.t-normal span[aria-hidden="true"]');
      if (degreeElement) {
        edu.degree = degreeElement.textContent.trim();
      }

      // Extract dates
      const dateElement = item.querySelector('.t-14.t-normal.t-black--light span[aria-hidden="true"]');
      if (dateElement) {
        edu.dateRange = dateElement.textContent.trim();
      }

      // Extract grade/activities
      const additionalInfo = item.querySelector('.pvs-list__outer-container');
      if (additionalInfo) {
        const activities = [];
        additionalInfo.querySelectorAll('li').forEach(li => {
          activities.push(li.textContent.trim());
        });
        if (activities.length > 0) {
          edu.activities = activities;
        }
      }

      // Extract school logo
      const logoImg = item.querySelector('img[class*="EntityPhoto"]');
      if (logoImg) {
        edu.schoolLogo = logoImg.src;
      }

      // Only add if we have at least a school name
      if (edu.school) {
        education.push(edu);
      }
    });

    return education;
  },

  // Extract detailed skills with endorsements
  extractDetailedSkills() {
    const skills = [];
    const skillsSection = document.querySelector('#skills');

    if (!skillsSection) {
      return skills;
    }

    const parent = skillsSection.closest('section');
    const items = parent?.querySelectorAll('.pvs-list__paged-list-item');

    items?.forEach(item => {
      const skill = {};

      // Extract skill name
      const nameElement = item.querySelector('[class*="t-bold"] span[aria-hidden="true"]');
      if (nameElement) {
        skill.name = nameElement.textContent.trim();
      }

      // Extract endorsement count
      const endorsementElement = item.querySelector('.t-14.t-normal.t-black--light');
      if (endorsementElement) {
        const text = endorsementElement.textContent.trim();
        const match = text.match(/(\d+)\s*endorsement/i);
        if (match) {
          skill.endorsements = parseInt(match[1]);
        }
      }

      // Only add if we have a skill name
      if (skill.name) {
        skills.push(skill);
      }
    });

    // Sort by endorsements if available
    skills.sort((a, b) => (b.endorsements || 0) - (a.endorsements || 0));

    return skills;
  },

  // Extract certifications
  extractCertifications() {
    const certifications = [];
    const certSection = document.querySelector('#licenses_and_certifications');

    if (!certSection) {
      return certifications;
    }

    const parent = certSection.closest('section');
    const items = parent?.querySelectorAll('.pvs-list__paged-list-item');

    items?.forEach(item => {
      const cert = {};

      // Extract certification name
      const nameElement = item.querySelector('[class*="t-bold"] span[aria-hidden="true"]');
      if (nameElement) {
        cert.name = nameElement.textContent.trim();
      }

      // Extract issuing organization
      const issuerElement = item.querySelector('.t-14.t-normal span[aria-hidden="true"]');
      if (issuerElement) {
        cert.issuer = issuerElement.textContent.trim();
      }

      // Extract issue date
      const dateElement = item.querySelector('.t-14.t-normal.t-black--light span[aria-hidden="true"]');
      if (dateElement) {
        cert.issueDate = dateElement.textContent.trim();
      }

      // Extract credential ID or URL
      const credentialLink = item.querySelector('a[href*="credential"]');
      if (credentialLink) {
        cert.credentialUrl = credentialLink.href;
      }

      if (cert.name) {
        certifications.push(cert);
      }
    });

    return certifications;
  },

  // Extract languages
  extractLanguages() {
    const languages = [];
    const langSection = document.querySelector('#languages');

    if (!langSection) {
      return languages;
    }

    const parent = langSection.closest('section');
    const items = parent?.querySelectorAll('.pvs-list__paged-list-item');

    items?.forEach(item => {
      const lang = {};

      // Extract language name
      const nameElement = item.querySelector('[class*="t-bold"] span[aria-hidden="true"]');
      if (nameElement) {
        lang.name = nameElement.textContent.trim();
      }

      // Extract proficiency
      const proficiencyElement = item.querySelector('.t-14.t-normal.t-black--light');
      if (proficiencyElement) {
        lang.proficiency = proficiencyElement.textContent.trim();
      }

      if (lang.name) {
        languages.push(lang);
      }
    });

    return languages;
  },

  // Extract recommendations received
  extractRecommendations() {
    const recommendationsSection = document.querySelector('#recommendations');

    if (!recommendationsSection) {
      return { count: 0, available: false };
    }

    // Try to get count from section header
    const headerText = recommendationsSection.textContent;
    const match = headerText.match(/(\d+)\s*recommendation/i);

    if (match) {
      return {
        count: parseInt(match[1]),
        available: true
      };
    }

    return { count: 0, available: true };
  },

  // Extract profile strength indicator
  extractProfileStrength() {
    // LinkedIn shows profile strength as a meter
    const strengthMeter = document.querySelector('[class*="profile-strength"]');

    if (strengthMeter) {
      const strengthText = strengthMeter.textContent.toLowerCase();

      if (strengthText.includes('all-star')) {
        return 'All-Star';
      } else if (strengthText.includes('expert')) {
        return 'Expert';
      } else if (strengthText.includes('advanced')) {
        return 'Advanced';
      } else if (strengthText.includes('intermediate')) {
        return 'Intermediate';
      } else if (strengthText.includes('beginner')) {
        return 'Beginner';
      }
    }

    return null;
  },

  // Utility function to try multiple selectors
  trySelectors(selectors) {
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && element.textContent) {
        const text = element.textContent.trim();
        if (text && text.length > 0) {
          return text;
        }
      }
    }
    return null;
  },

  // Parse search results for batch operations
  parseSearchResults() {
    const results = [];
    const resultCards = document.querySelectorAll('.entity-result__item, .reusable-search__result-container');

    resultCards.forEach(card => {
      const result = {};

      // Extract profile URL
      const profileLink = card.querySelector('a[href*="/in/"]');
      if (profileLink) {
        result.linkedinUrl = profileLink.href.split('?')[0]; // Remove query params
      }

      // Extract name
      const nameElement = card.querySelector('.entity-result__title-text span[aria-hidden="true"]');
      if (nameElement) {
        result.name = nameElement.textContent.trim();
      }

      // Extract headline/title
      const headlineElement = card.querySelector('.entity-result__primary-subtitle');
      if (headlineElement) {
        result.headline = headlineElement.textContent.trim();
      }

      // Extract location
      const locationElement = card.querySelector('.entity-result__secondary-subtitle');
      if (locationElement) {
        result.location = locationElement.textContent.trim();
      }

      // Extract profile picture
      const imgElement = card.querySelector('img.presence-entity__image');
      if (imgElement) {
        result.profilePicture = imgElement.src;
      }

      // Extract mutual connections
      const mutualElement = card.querySelector('.entity-result__insights span');
      if (mutualElement && mutualElement.textContent.includes('mutual')) {
        result.mutualConnections = mutualElement.textContent.trim();
      }

      // Only add if we have at least a LinkedIn URL
      if (result.linkedinUrl) {
        results.push(result);
      }
    });

    return results;
  }
};

// Make LinkedInParser available globally in content script
window.LinkedInParser = LinkedInParser;